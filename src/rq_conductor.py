from redis import Redis
from rq import Queue
from rq.job import JobStatus

from utils import terminal_run


class RQConductor:
    def __init__(
        self,
        basename: str,
        count: int = 3,
        auto_start: bool = True,
        worker: str = "worker.py",
    ):
        # Start RQ workers
        if auto_start:
            for i in range(count):
                terminal_run(f"python {worker} {basename}{i}")

        # Setup queues
        self.queues = [
            Queue(f"{basename}{i}", connection=Redis()) for i in range(count)
        ]
        self.current_queue = 0
        self.max_queue = count

        self.jobs = []

    def enqueue_job(self, function: callable, *args, **kwargs):
        self.jobs.append(
            self.queues[self.current_queue].enqueue(function, *args, **kwargs)
        )

        self.current_queue = (self.current_queue + 1) % self.max_queue

    def update(self, finish_callback: callable = None):
        finished_jobs = []

        for job in self.jobs:
            match job.get_status():
                case JobStatus.FINISHED:
                    if finish_callback:
                        finish_callback(job.id, job.result)

                    # Mark job as finished
                    finished_jobs.append(job)

                case _:
                    pass

        # Remove finished jobs
        for job in finished_jobs:
            self.jobs.remove(job)
