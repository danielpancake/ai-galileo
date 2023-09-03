from director import generate_full_story
from dotenv import load_dotenv
from loguru import logger
from pymongo import MongoClient

from redis import Redis
from rq import Queue
from rq.job import JobStatus

import argparse
import os
import pytchat
import re
import toml


load_dotenv()

QUEUE_STORIES = "stories"


class StatusCodes:
    ADDED = "added"
    QUEUED = "queued"
    COMPLETED = "completed"
    FAILED = "failed"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="ai-galileo",
        description="AI Galileo is a chatbot that generates stories based on user-submitted topics.",
    )
    parser.add_argument("--clean", help="Clean the database", action="store_true")
    parser.add_argument("--verbose", help="Verbose logging", action="store_true")

    args = parser.parse_args()

    # Setup Redis queue
    q_stories = Queue(QUEUE_STORIES, connection=Redis())
    topics_jobs = []

    # Setup MongoDB
    mongo_client = MongoClient(os.environ.get("MONGO_URI"))
    db = mongo_client["ai-galileo"]

    if args.clean:
        # Clear submission topics and stories from previous runs
        db["submission_topics"].delete_many({})
        db["stories"].delete_many({})

    # Load director config
    director_config = toml.load("director.toml")

    # Setup YouTube chat listener
    chat = pytchat.create(os.environ.get("STREAM_ID"))

    while True:
        # Poll chat for new topic submissions
        if chat.is_alive():
            for c in chat.get().sync_items():
                if not re.search(r"!topic", c.message):
                    continue

                theme = re.sub(r"!topic", "", c.message).strip()

                if args.verbose:
                    logger.info(f"New topic submission: {theme}")

                # Add to submission topics
                db["submission_topics"].insert_one(
                    {
                        "theme": theme,
                        "requested_by": c.author.name,
                        "status": StatusCodes.ADDED,
                    }
                )

        # Process new topics
        for topic in db["submission_topics"].find({"status": StatusCodes.ADDED}):
            job = q_stories.enqueue(
                generate_full_story,
                args=(director_config, topic["theme"]),
                job_timeout=3600,
            )

            # Update status
            db["submission_topics"].update_one(
                {"_id": topic["_id"]}, {"$set": {"status": StatusCodes.QUEUED}}
            )

            topics_jobs.append(
                {
                    "_id": topic["_id"],
                    "job": job,
                }
            )

        # Check status of jobs
        finished_jobs = []

        for topic_job in topics_jobs:
            job = topic_job["job"]

            match job.get_status():
                case JobStatus.FINISHED:
                    job_result = job.return_value()

                    # Update status
                    db["submission_topics"].update_one(
                        {"_id": topic_job["_id"]},
                        {"$set": {"status": StatusCodes.COMPLETED}},
                    )

                    # Retrieve who asked
                    requested_by = db["submission_topics"].find_one(
                        {"_id": topic_job["_id"]}
                    )["requested_by"]

                    # Add to stories
                    db["stories"].insert_one(
                        {
                            "theme": job_result["theme"],
                            "story": job_result["story"],
                            "pre_story": job_result["pre_story"],
                            "post_story": job_result["post_story"],
                            "requested_by": requested_by,
                        }
                    )

                    # Mark job for removal
                    finished_jobs.append(job)

                case _:
                    pass

        # Remove finished jobs
        for job in finished_jobs:
            topics_jobs.remove(job)

            # Remove from submission topics
            db["submission_topics"].delete_one({"_id": job["_id"]})
