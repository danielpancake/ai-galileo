# Training custom tts with Piper

This tutorial is made by our team in order to help reproduce our results of Pushnoy-model. We will use
[piper-tts](https://github.com/rhasspy/piper/tree/master) model's architecture as it's new, stable, light and
most importantly high-quality text-to-speech (not monotonic / too synthetic).

### Navigation

- [Installation](#installation)
  - [OS requirements](#os-requirements)
  - [Environment](#setting-up-environment)
- [Creating Dataset](#creating-dataset)
  - [Transcribing audio](#transcribing-raw-data)
  - [Slicing dataset](#slicing-the-dataset-and-converting-to-ljspeech)
- [Preprocessing & Training](#preprocessing-and-training)
  - [Preprocessing](#preprocessing)
  - [Download checkpoint](#downloading-pretrained-checkpoint)
  - [Training](#training)
  - [Testing](#testing-model)
- [Upload model](#uploading-model-to-hugging-face)
  - [Exporting model](#exporting-model)
  - [Piper-styled repository](#setting-up-piper-styled-hierarchy)
  - [Upload to hugging-face](#uploading-model-to-hugging-face)
- [Inference](#inference)
  - [Download model](#download-model-from-hugging-face)
  - [Inference with any sentence](#inference-with-custom-text)

# Installation

### OS and Hardware requirements

- Linux or [WSL](https://learn.microsoft.com/en-us/windows/wsl/install)
- NVIDIA GPU with CUDA support (preferably, but not required)

### Setting up environment

#### WSL Installation

If you are using Windows, you can install WSL by following [this guide](https://learn.microsoft.com/en-us/windows/wsl/install), which will be briefly summarized here.

1. Open PowerShell as Administrator and run the following command:

```powershell
wsl --update
wsl --set-default-version 2

wsl --install
```

In case you get any errors, please, refer to [this guide](https://learn.microsoft.com/en-us/windows/wsl/install-manual).

2. After the installation is complete, you can open the Ubuntu terminal and proceed with the next step -- installing required packages.

```shell
sudo apt update
sudo apt dist-upgrade -y
sudo apt install python3-dev python3.10-venv espeak-ng ffmpeg build-essential -y
```

#### Python environment

We will create a virtual environment for Python packages, so that they don't interfere with the system packages.

```shell
cd ~/

git clone https://github.com/rhasspy/piper.git

python3 -m venv ~/piper/src/python/.venv

cd ~/piper/src/python/
source ~/piper/src/python/.venv/bin/activate

python3 -m pip install --upgrade pip
python3 -m pip install --upgrade wheel setuptools
python3 -m pip install -e .
sudo bash ~/piper/src/python/build_monotonic_align.sh
```

# Creating dataset

### Transcribing raw data

Ideal way to transcribe data is to hire person and mark all text manually. However, for our case
we decided to use a bit more automatic approach by using [Whisper-large-v2](https://huggingface.co/openai/whisper-large-v2) model,
to be more precise [faster-whisper-large-v2](https://huggingface.co/guillaumekln/faster-whisper-large-v2) as it's more optimized.

In order to do this we wrote simple python script `transcribe.py` that requires at pure minimum
single input audio file and main language used there. There are also some additional parameters
such as `--model`, `--device`, `--output`, `--append` for which you can see usage/documentation
by writing `python3 transcriber.py -h` in the console.

```shell
python3 transcribe.py \
  --file voice-samples.mp3 \
  --output transcription.txt\
  --language ru
```

This command will generate file `transcription.txt` with timestamps and transcriptions in original file.

### Slicing the dataset and converting to ljspeech

Now we need to split the source audio file using the generated transcriptions.
We wrote a Rust program to parse the transcriptions file and for every line it calls a small python script to actually cut the audio.

For this step, make sure you have [Rust](https://www.rust-lang.org) and [ffmpeg](https://www.ffmpeg.org) installed on your system.
If you have [Nix](https://nixos.org) you can use the flake in the `utils/split_audio` directory via `nix develop` or `direnv allow` to also create an new python venv.

Also make sure to install [pydub](https://github.com/jiaaro/pydub): `python3 -m pip install pydub`

Once you have all the dependencies, you should be able to run the program with cargo by providing paths to the audio file and to the transcription file.

```shell
cd utils/split_audio
cargo run -- voice-samples.mp3 transcription.txt
```

It should generate the output in the `out/` directory with the cut audio in the `audio/` directory and an `ids.csv` file mapping ids (names) of the audio files to their corresponding transcription.

In order to make dataset fully `ljspeech` format, rename `audio/ -> wav/` and `ids.csv -> metadata.csv`.

# Preprocessing and training

### Preprocessing

Now when you have raw dataset it's important to preprocess it. In order to do this you should
run next commands in console:

It's highly recommended to have all datasets in `datasets` folder, and all training in `training`.
So let's create them:

```shell
mkdir "datasets"
mkdir "training"
```

Then you need to move your raw dataset into `datasets/` folder. Just to check evething is alright,
make sure your file structure is looking the same way:

```
piper
└─── etc
└─── lib
└─── notebooks
└─── src
└─── training
     └─── !!YOUR_DATASET_NAME!!
└─── datasets
     └─── !!YOUR_DATASET_NAME!!
         │    metadata.csv
         └─── wav
              └─── 000.wav
              └─── 001.wav
              ...
```

If it's true, you are ready to start.

Activate env and download all required libraries

```shell
# add environment variable to .bashrc
echo 'export LD_LIBRARY_PATH=/usr/lib/wsl/lib:$LD_LIBRARY_PATH' >> ~/.bashrc

python3 -m venv ~/piper/src/python/.venv

cd ~/piper/src/python/
source ~/piper/src/python/.venv/bin/activate

python3 -m pip install --upgrade pip
python3 -m pip install --upgrade wheel setuptools
python3 -m pip install -e .
sudo bash ~/piper/src/python/build_monotonic_align.sh

# downgrade torchmetrics as in newer version there is a bug
# https://github.com/AUTOMATIC1111/stable-diffusion-webui/issues/11648
python3 -m pip install torchmetrics==0.11.4
```

And when you are done, you can finally run preprocessing script. Replace `**` variables with your values.

```shell
cd ~/piper/src/python/

python3 -m piper_train.preprocess \
  --language **ru** \
  --input-dir ~/piper/datasets/[YOUR_DATASET] \
  --output-dir ~/piper/training/[YOUR_OUTPUT_DIR] \
  --dataset-format ljspeech \
  --single-speaker \
  --sample-rate 22050

```

### Downloading pretrained checkpoint

It's optional step, you can skip it. However, we strongly suggest to use some pretrained checkpoints
as it will significantly boost your speed of training. You can download any piper checkpoint
(`epoch=XXXX-step=XXXXXXX.ckpt` file) from their official
[hugging-face page](https://huggingface.co/datasets/rhasspy/piper-checkpoints/tree/main).

You are not obliged to use the same language, as models use phonemes, not alphabet as base. However,
it is recommended to use same-family languages as accent may be translated from original checkpoint.
In our case we used `ru_RU-dmitri-medium` as checkpoint to start from as it provided most similar
target intonation.

### Training

We suppose that you already activated environment as described in [preprocessing](#preprocessing)
step, so all you need to do is to write next command:

```shell
cd ~/piper/src/python/

python3 -m piper_train \
    --dataset-dir ~/piper/training/[YOUR_DATASET] \
    --accelerator 'gpu' \
    --devices 1 \
    --batch-size 16 \
    --validation-split 0.0 \
    --num-test-examples 0 \
    --max_epochs 6000 \
    --resume_from_checkpoint ~/piper/epoch=XXXX-step=XXXXXXX.ckpt \
    --checkpoint-epochs 1 \
    --precision 32
```

If you don't want to start from checkpoint, remove `--resume_from_checkpoint` argument, also make sure
that `--max_epochs` suits your need. As we used dmitri 6000 was enough for an initial test. You may
need to change that number according to your need.

Worth mentioning: on NVIDIA 2080 Super Mobile GPU each epoch takes ~22 seconds. You can use
this value as starting point to approximate training time.

In our case we trained for 900 epochs total with final epoch being 6500.

### Testing model

If you want to test how model performs, you can easily do it by downloading test !!`.jsonl`!! files from
[piper repository](https://github.com/rhasspy/piper/tree/master/etc/test_sentences) and running next command:

```shell
cat ~/piper/test_[LANGUAGE].jsonl | \
    python3 -m piper_train.infer \
        --sample-rate 22050 \
        --checkpoint ~/piper/training/[YOUR_DATASET]/lightning_logs/version_[VERSION_NUMBER]/checkpoints/*.ckpt \
        --output-dir ~/piper/training/[YOUR_DATASET]/output
```

# Uploading model to Hugging Face

### Exporting model

After you finished training, you can convert your checkpoint model to final .onnx file with simple command

```shell
mkdir ~/piper/[YOUR_MODEL]

python3 -m piper_train.export_onnx \
    ~/piper/training/[YOUR_DATASET]/lightning_logs/version_[VERSION_NUMBER]/checkpoints/epoch=5589-step=1382940.ckpt \
    ~/piper/[YOUR_MODEL]/[LANGUAGE]-[MODEL_NAME]-medium.onnx

cp ~/piper/training/[YOUR_DATASET]/config.json \
   ~/piper/[YOUR_MODEL]/[LANGUAGE]-[MODEL_NAME]-medium.onnx.json
```

### Setting up piper-styled hierarchy

In order to upload your model to hugging face we suggest to make you model the save hierarchy
as other piper-based projects. It includes having `.onnx` and `.onnx.json` files which you already have.
`MODEL_CARD` file with model description and `voices.json` file with all your models. So let's start from `MODEL_CARD`.

Create `MODEL_CARD` file in `~/piper/[YOUR_MODEL]` directory with next content

```text
# Model card for [MODEL_NAME] (medium)

* Language: [LANGUAGE_CODE]
* Speakers: 1
* Quality: medium
* Samplerate: 22,050Hz

## Dataset

* URL: [INSERT URL]
* License: [INSERT LICENSE]

## Training

Finetuned from [LANGUAGE-DIALECT]. [MODEL YOU BASED YOUR SOLUTION ON] (medium quality).
```

And final part is to make `voices.json` file that will describe all your trained models. It is
important to have such file even if you trained one model as it will be parsed when someone will
download your model.

File containing inside just path's to each file, so you can define them yourself. We will just show you
an example how our Pushnoy model look like in it.

P.S. You can get `md5 hash` by running `sudo md5sum filename`. \
P.P.S. You can get `size_bytes` by running `wc -c < filename`.

```json
// voices.json file
{
  "ru_RU-pushnoy-medium": {
    "name": "pushnoy",
    "language": "ru_RU",
    "quality": "medium",
    "num_speakers": 1,
    "speaker_id_map": {},
    "files": {
      "ru_RU-pushnoy-medium.onnx": {
        "size_bytes": 63511038,
        "md5_digest": "ac01e25a9c6da1fe8af8f921cb7a833b"
      },
      "ru_RU-pushnoy-medium.onnx.json": {
        "size_bytes": 7094,
        "md5_digest": "2e679f7839293f9412bf1e2973fe1138"
      },
      "MODEL_CARD": {
        "size_bytes": 309,
        "md5_digest": "d6b3806b0f121ad01360d6fe81952064"
      }
    }
  }
}
```

### Upload model to hugging-face

Upload all your files to [hugging face](https://huggingface.co/). Make sure to make your
model and files public and add description!

Our [Pushnoy model](https://huggingface.co/cutefluffyfox/pushnoy-piper-tts/tree/main) as an example.

# Inference

### Download model from Hugging Face

To simply download pyper-styled models from hugging-face we wrote `pushnoy-tts/downloader.py` script.
You can download your model by hand by writing next code or just skipping this part and run `inferece.py` script.

```python
from downloader import PiperDownloader

model_name = 'ru_RU-pushnoy-medium'
huggingface_repo = 'cutefluffyfox/pushnoy-piper-tts'

PiperDownloader(model_name, repo_id=huggingface_repo).download()
```

### Inference with custom text

Inference is also pretty simple as we already wrote script for it. You can modify `pushnoy-tts/inference.py`
file with your `model_name`, `repo_id`, `language` and `text`. That's enough to generate any audio with your
custom TTS model!
