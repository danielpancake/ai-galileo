from pydub import AudioSegment


# Load trim points and file names
trim_points = []
files = []

with open("out/trim-points.txt", "r") as f:
    for line in f.readlines():
        # Format is "file_name.wav:trim_point"
        file, trim_point = line.split(":")
        trim_points.append(float(trim_point))
        files.append(file)

        print(file, float(trim_point))

# Split the combined file
combined = AudioSegment.from_file("rvc-out/audio.mp3")

for idx, (trim_point, file) in enumerate(zip(trim_points, files)):
    # Get the start and end points
    start = 0 if idx == 0 else trim_points[idx - 1]
    end = trim_point

    # Export the file
    combined[start * 1000 : end * 1000].export("rvc-out/" + file, format="mp3")
