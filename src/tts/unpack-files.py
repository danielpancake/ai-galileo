from os import listdir, makedirs
from os.path import isfile, join
from pydub import AudioSegment

# Get all out folders
folders = [f for f in listdir("out") if not isfile(join("out", f))]

# TODO: make this a function with a folder parameter
for folder in folders:
    # Load trim points and file names
    trim_points = []
    files = []

    with open(f"out/{folder}/trim-points.txt", "r") as f:
        for line in f.readlines():
            # Format is "file_name.ext:trim_point"
            file, trim_point = line.split(":")
            trim_points.append(float(trim_point))
            files.append(file)

    # Split the combined file
    combined = AudioSegment.from_file(f"out/{folder}/combined-rvc.wav")

    makedirs(f"rvc-out/{folder}", exist_ok=True)

    for idx, (trim_point, file) in enumerate(zip(trim_points, files)):
        # Get the start and end points
        start = 0 if idx == 0 else trim_points[idx - 1]
        end = trim_point

        # Export the file
        combined[start * 1000 : end * 1000].export(
            f"rvc-out/{folder}/{file}", format="mp3"
        )
