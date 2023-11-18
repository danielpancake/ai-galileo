from voice_gen.inference import init_global_piper_model

from rq import Connection, SimpleWorker
from rq_win import WindowsWorker

import os
import sys

"""A worker that preloads piper model and then starts working."""
with Connection():
    qs = sys.argv[1:] or ["default"]

    # Preload piper model
    print("Preloading piper model...")
    init_global_piper_model("ru_RU-pushnoy-medium")

    # Use WindowsWorker if on Windows, otherwise use SimpleWorker
    w = WindowsWorker(qs) if os.name == "nt" else SimpleWorker(qs)
    w.work()
