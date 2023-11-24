import logging

# All voice-cloning related libraries
from downloader import PiperDownloader
from piper import Piper


# Configure logging
FORMAT = "%(asctime)s : %(message)s"
logging.basicConfig(format=FORMAT, level=logging.INFO)

# Define all required key variables
speech_speed = 1
output_file = "tts-sts.wav"
model = "ru_RU-pushnoy-medium"
text = "Я ничего не боюсь, Марго, - вдруг ответил ей мастер и поднял голову и показался ей таким, каким был, когда сочинял то, чего никогда не видал, но о чём наверно знал, что оно было, - и не боюсь, потому что я всё уже испытал."

# Download models
PiperDownloader(model, repo_id="cutefluffyfox/pushnoy-piper-tts").download()

# Define all models (after downloading)
piper = Piper(model, use_cuda="auto")

# Full pipeline
piper.synthesize_and_save(text, output_file=output_file, length_scale=1 / speech_speed)
