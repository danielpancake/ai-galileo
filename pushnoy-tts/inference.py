# python build-in libraries
import logging

# all voice-cloning related libraries
from downloader import PiperDownloader
from piper import Piper


# Configure logging
FORMAT = '%(asctime)s : %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)


# Define all required key variables
speech_speed = 1.6
output_file = 'tts-sts.wav'
model = 'ru_RU-pushnoy-medium'
text = "Привет дорогие друзья! Вы должны знать как сильно я вас люблю! Вы мои лапочки, солнышки и конечно же сатанисты. Э"


# Download models
PiperDownloader(model, repo_id='cutefluffyfox/pushnoy-piper-tts').download()


# Define all models (after downloading)
piper = Piper(model, use_cuda='auto')

# Full pipeline
piper.synthesize_and_save(text, output_file=output_file, length_scale=speech_speed)
