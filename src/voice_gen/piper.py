# This code is taken and partially modified from Piper official repository under MIT Licence
# https://github.com/rhasspy/piper/blob/master/src/python_run/piper/__init__.py

from dataclasses import dataclass
from pathlib import Path
from typing import List, Mapping, Optional, Sequence, Union

from espeak_phonemizer import Phonemizer

import numpy as np
import onnxruntime
import torch.cuda

import io
import os
import json
import logging
import wave

from .downloader import Downloader

# TODO: fix this import


_LOGGER = logging.getLogger(__name__)

_BOS = "^"
_EOS = "$"
_PAD = "_"


@dataclass
class PiperConfig:
    num_symbols: int
    num_speakers: int
    sample_rate: int
    espeak_voice: str
    length_scale: float
    noise_scale: float
    noise_w: float
    phoneme_id_map: Mapping[str, Sequence[int]]


class Piper:
    def __init__(self, model: str, use_cuda: Union[bool, str] = "auto"):
        model_path = os.path.join(
            Downloader.models_path, "Piper", model, model + ".onnx"
        )
        config_path = f"{model_path}.json"

        if use_cuda == "auto":
            use_cuda = torch.cuda.is_available()

        if not os.path.exists(config_path):
            raise FileNotFoundError(
                f"Model {model} is not downloaded yet, please download it "
                f"first by PiperDownloader class"
            )

        self.config = load_config(config_path)
        self.phonemizer = Phonemizer(self.config.espeak_voice)
        self.model = onnxruntime.InferenceSession(
            str(model_path),
            sess_options=onnxruntime.SessionOptions(),
            providers=["CPUExecutionProvider"]
            if not use_cuda
            else ["CUDAExecutionProvider"],
        )

    def synthesize(
        self,
        text: str,
        speaker_id: Optional[int] = 0,
        length_scale: Optional[float] = None,
        noise_scale: Optional[float] = None,
        noise_w: Optional[float] = None,
    ) -> bytes:
        """Synthesize WAV audio from text"""
        if length_scale is None:
            length_scale = self.config.length_scale

        if noise_scale is None:
            noise_scale = self.config.noise_scale

        if noise_w is None:
            noise_w = self.config.noise_w

        phonemes_str = self.phonemizer.phonemize(text, keep_clause_breakers=True)
        phonemes = [_BOS] + list(phonemes_str)
        phoneme_ids: List[int] = []

        for phoneme in phonemes:
            if phoneme in self.config.phoneme_id_map:
                phoneme_ids.extend(self.config.phoneme_id_map[phoneme])
                phoneme_ids.extend(self.config.phoneme_id_map[_PAD])
            else:
                _LOGGER.warning("No id for phoneme: %s", phoneme)

        phoneme_ids.extend(self.config.phoneme_id_map[_EOS])

        phoneme_ids_array = np.expand_dims(np.array(phoneme_ids, dtype=np.int64), 0)
        phoneme_ids_lengths = np.array([phoneme_ids_array.shape[1]], dtype=np.int64)
        scales = np.array([noise_scale, length_scale, noise_w], dtype=np.float32)

        # Synthesize through Onnx
        audio = self.model.run(
            None,
            {
                "input": phoneme_ids_array,
                "input_lengths": phoneme_ids_lengths,
                "scales": scales,
                "sid": None
                if self.config.num_speakers == 1
                else np.array(
                    [0 if speaker_id is None else speaker_id], dtype=np.int64
                ),
            },
        )[0].squeeze((0, 1))
        audio = audio_float_to_int16(audio.squeeze())

        # Convert to WAV
        with io.BytesIO() as wav_io:
            wav_file: wave.Wave_write = wave.open(wav_io, "wb")
            with wav_file:
                wav_file.setframerate(self.config.sample_rate)
                wav_file.setsampwidth(2)
                wav_file.setnchannels(1)
                wav_file.writeframes(audio.tobytes())

            return wav_io.getvalue()

    def synthesize_and_save(self, text: str, output_file: str, **kwargs):
        """Just decorator for synthesize function and saving it to file"""
        out = self.synthesize(text, **kwargs)
        with open(output_file, "wb") as file:
            if output_file.endswith(".wav"):
                file.write(out)
            elif output_file.endswith(".mp3"):
                import pydub
                from pydub import AudioSegment
                from pydub.playback import play

                audio_segment = AudioSegment.from_wav(io.BytesIO(out))
                audio_segment.export(output_file, format="mp3")
            else:
                raise ValueError("Unsupported file format")


def load_config(config_path: Union[str, Path]) -> PiperConfig:
    """Loads model config file & parse all required info"""
    with open(config_path, "r", encoding="utf-8") as config_file:
        config_dict = json.load(config_file)
        inference = config_dict.get("inference", {})

        return PiperConfig(
            num_symbols=config_dict["num_symbols"],
            num_speakers=config_dict["num_speakers"],
            sample_rate=config_dict["audio"]["sample_rate"],
            espeak_voice=config_dict["espeak"]["voice"],
            noise_scale=inference.get("noise_scale", 0.667),
            length_scale=inference.get("length_scale", 1.0),
            noise_w=inference.get("noise_w", 0.8),
            phoneme_id_map=config_dict["phoneme_id_map"],
        )


def audio_float_to_int16(
    audio: np.ndarray, max_wav_value: float = 32767.0
) -> np.ndarray:
    """Normalize audio and convert to int16 range"""
    audio_norm = audio * (max_wav_value / max(0.01, np.max(np.abs(audio))))
    audio_norm = np.clip(audio_norm, -max_wav_value, max_wav_value)
    audio_norm = audio_norm.astype("int16")
    return audio_norm
