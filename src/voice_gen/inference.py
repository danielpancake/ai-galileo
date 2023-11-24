from .downloader import PiperDownloader
from .piper import Piper

# TODO: fix this import

import os


def init_global_piper_model(model: str):
    """Initialize the global Piper model"""
    PiperDownloader(model, repo_id="cutefluffyfox/pushnoy-piper-tts").download()

    global __piper_model
    __piper_model = Piper(model, use_cuda="auto")


def synthesize(
    text: str,
    output_file: str,
    speech_speed: float = 1.15,
):
    """Synthesize the voice for a line of text"""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    return __piper_model.synthesize_and_save(
        text,
        output_file,
        length_scale=1 / speech_speed,
    )


def voice_episode(episode: dict):
    """Synthesize the voice for an episode"""
    for sequence_type in ["story_intro", "story", "story_outro"]:
        for line in episode[sequence_type]:
            if line["type"] == "text":
                synthesize(
                    line["text"] + "...",  # Add pause at the end of the line
                    line["voice"],
                )
