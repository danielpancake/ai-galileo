from os import listdir
from os.path import isfile, join
from pydub import AudioSegment

# Get all out folders
folders = [f for f in listdir("out") if not isfile(join("out", f))]

# TODO: make this a function with a folder parameter
for folder in folders:
    files = []
    for sequence in ["pre_story", "story", "post_story"]:
        files.extend(
            [
                f
                for f in listdir(f"out/{folder}")
                if isfile(join(f"out/{folder}", f)) and f.startswith(sequence)
            ]
        )

    files = [f for f in files if f.endswith(".mp3")]

    # Concatenate all files into one
    combined = AudioSegment.empty()

    # Save trim points
    trim_points = []

    for file in files:
        combined += AudioSegment.from_file(f"out/{folder}/{file}")
        trim_points.append(combined.duration_seconds)

    # Export the combined file
    combined.export(f"out/{folder}/combined.wav", format="wav")

    # Save trim points with file names
    with open(f"out/{folder}/trim-points.txt", "w") as f:
        # Format is "file_name.wav:trim_point"
        for i in range(len(trim_points)):
            f.write(files[i] + ":" + str(trim_points[i]) + "\n")
