from faster_whisper import WhisperModel

import torch
import logging
import argparse


logger = logging.getLogger("whisper")
logger.setLevel(level=logging.INFO)

logger.info("Initializing whisper model")

MODELS = [
    "tiny",
    "tiny.en",
    "base",
    "base.en",
    "small",
    "small.en",
    "medium",
    "medium.en",
    "large-v1",
    "large-v2",
]

MODEL_PARAMETERS = {"compute_type": "float16", "device": "cuda"}
TRANS_PARAMETERS = {
    "language": "ru",
    "task": "transcribe",
    "beam_size": 5,
    "best_of": 5,
    "patience": 1,
    "length_penalty": 1,
    "temperature": [
        0.0,
        0.2,
        0.4,
        0.6,
        0.8,
        1.0,
    ],
    "compression_ratio_threshold": 2.4,
    "log_prob_threshold": -1.0,
    "no_speech_threshold": 0.6,
    "condition_on_previous_text": True,
    "initial_prompt": None,
    "prefix": None,
    "suppress_blank": True,
    "suppress_tokens": [-1],
    "without_timestamps": False,
    "max_initial_timestamp": 1.0,
    "word_timestamps": True,
    "prepend_punctuations": "\"'“¿([{-",
    "append_punctuations": "\"'.。,，!！?？:：”)]}、",
    "vad_filter": False,
    "vad_parameters": None,
}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Transcriber",
        description="By giving audio and model type transcribes such model with Faster-whisper",
    )

    parser.add_argument(
        "-f", "--file", required=True, help="Filename of audio file to be transcribed"
    )
    parser.add_argument(
        "-l", "--language", required=True, help="Main language used in audio file"
    )
    parser.add_argument(
        "-m",
        "--model",
        default=MODELS[-1],
        choices=MODELS,
        help="Whisper-model size to use",
    )
    parser.add_argument(
        "-d",
        "--device",
        default="auto",
        choices=["cpu", "cuda", "auto"],
        help="Device on which to load model",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="transcription.txt",
        help="Output file with transcription",
    )
    parser.add_argument(
        "-a",
        "--append",
        action="store_true",
        help="If added file would be appended, not rewritten",
    )

    args = parser.parse_args()

    if args.device == "auto":
        args.device = "cuda" if torch.cuda.is_available() else "cpu"

    MODEL_PARAMETERS["device"] = args.device
    TRANS_PARAMETERS["language"] = args.language

    model = WhisperModel(args.model, **MODEL_PARAMETERS)

    logger.info("Starting transcription")
    segments, info = model.transcribe(args.file, **TRANS_PARAMETERS)

    if not args.append:
        with open(args.output, "w", encoding="UTF-8"):
            pass

    for segment in segments:
        with open(args.output, "a", encoding="UTF-8") as file:
            print(
                "[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text),
                file=file,
            )
            logger.info(
                "[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text)
            )

    logger.info("Transcription successfully done and saved to transcription.txt")
