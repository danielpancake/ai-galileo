from downloader import PiperDownloader
from piper import Piper


def init_global_piper_model(model: str) -> None:
    PiperDownloader(model, repo_id="cutefluffyfox/pushnoy-piper-tts").download()

    global __piper_model
    __piper_model = Piper(model, use_cuda="auto")


def synthesize(
    text: str,
    output_file: str,
    speech_speed: float = 1.25,
    length_scale: float = 1.0,
) -> None:
    return __piper_model.synthesize_and_save(
        text,
        output_file,
        length_scale=1 / speech_speed,
    )
