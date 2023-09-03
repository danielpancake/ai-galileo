from dotenv import load_dotenv

from rq import Connection
from rq_win import WindowsWorker

import sys

with Connection():
    qs = sys.argv[1:] or ["default"]

    load_dotenv()

    w = WindowsWorker(qs)
    w.work()
