from bson import ObjectId
from redis import Redis
from rq import Queue
from rq.job import JobStatus

from utils import terminal_run


class RQConductor:
    def __init__(
        self,
        basename: str,
        worker: str,
        auto_start: bool = True,
        count: int = 3,
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

    def update(self) -> list:
        result = []
        finished_jobs = []

        for job in self.jobs:
            match job.get_status():
                case JobStatus.FINISHED:
                    result.append((ObjectId(job.id), job.result))
                    finished_jobs.append(job)

                case _:
                    pass

        # Remove finished jobs
        for job in finished_jobs:
            self.jobs.remove(job)

        return result
