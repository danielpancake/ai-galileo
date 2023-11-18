from dotenv import load_dotenv

from rq import Connection, SimpleWorker
from rq_win import WindowsWorker

import os
import sys

"""A simple worker that loads the .env file and then starts working."""
with Connection():
    qs = sys.argv[1:] or ["default"]

    load_dotenv()

    # Use WindowsWorker if on Windows, otherwise use SimpleWorker
    w = WindowsWorker(qs) if os.name == "nt" else SimpleWorker(qs)
    w.work()
