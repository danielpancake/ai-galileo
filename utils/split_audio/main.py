from pydub import AudioSegment

source = None


def load(path):
    global source
    source = AudioSegment.from_mp3(path)


def cut_audio(target, cut_from, cut_to):
    global source
    source[cut_from:cut_to].export(target, format="wav")
