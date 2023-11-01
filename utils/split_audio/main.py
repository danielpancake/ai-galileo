from pydub import AudioSegment

def cut_audio(source, target, cut_from, cut_to):
    source = AudioSegment.from_mp3(source)
    source = source[cut_from:cut_to]
    source.export(target, format="mp3")

