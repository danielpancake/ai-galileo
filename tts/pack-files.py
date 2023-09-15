from os import listdir
from os.path import isfile, join
from pydub import AudioSegment


# Get all files in the output folder
files = [f for f in listdir("out") if isfile(join("out", f))]
files = [f for f in files if f.endswith(".mp3")]
files = [f for f in files if "story" in f]

# Concatenate all files into one
combined = AudioSegment.empty()

# Save trim points
trim_points = []

for file in files:
    combined += AudioSegment.from_file("out/" + file)
    trim_points.append(combined.duration_seconds)

# Export the combined file
combined.export("out/combined.wav", format="wav")

# Save trim points with file names
with open("out/trim-points.txt", "w") as f:
    # Format is "file_name.wav:trim_point"
    for i in range(len(trim_points)):
        f.write(files[i] + ":" + str(trim_points[i]) + "\n")
