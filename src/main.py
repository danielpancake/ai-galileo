from director import generate_full_story
from dotenv import load_dotenv
from loguru import logger
from pymongo import MongoClient, errors
from utils import StatusCodes, run_in_terminal

from redis import Redis
from rq import Queue
from rq.job import JobStatus

import argparse
import os
import pytchat
import re
import toml


QUEUE_STORIES_BASENAME = "stories"


def setup_args():
    """Setup command line arguments."""
    parser = argparse.ArgumentParser(
        prog="ai-galileo",
        description="AI Galileo is a chatbot that generates stories based on user-submitted topics.",
    )
    parser.add_argument("--clean", help="Clean the database", action="store_true")
    parser.add_argument("--verbose", help="Verbose logging", action="store_true")
    parser.add_argument("--rq-start", help="Run RQ workers", action="store_true")
    parser.add_argument("--rq-count", help="Number of RQ workers", type=int, default=3)
    parser.add_argument(
        "--local-theme",
        help="Generate a story locally. Disables YouTube chat listener",
        type=str,
        default=None,
    )

    return parser.parse_args()


if __name__ == "__main__":
    load_dotenv()
    args = setup_args()

    # Start RQ workers
    if args.rq_start:
        for i in range(args.rq_count):
            run_in_terminal(f"python worker.py {QUEUE_STORIES_BASENAME}{i}")

            if args.verbose:
                logger.info(f"Started worker for {QUEUE_STORIES_BASENAME}{i}")

    # Setup Redis queues
    q_stories_list = [
        Queue(f"{QUEUE_STORIES_BASENAME}{i}", connection=Redis())
        for i in range(args.rq_count)
    ]
    q_stories_current = 0

    topics_jobs = []

    try:
        # Setup MongoDB
        mongo_client = MongoClient(os.environ.get("MONGO_URI"))
        mongo_client.server_info()
    except errors.ServerSelectionTimeoutError as err:
        logger.error(err)
        exit(1)

    if args.verbose:
        logger.info("Connected to MongoDB")

    db = mongo_client["ai-galileo"]

    # Clear submission topics and stories from previous runs
    if args.clean:
        db["submission_topics"].delete_many({})
        db["stories"].delete_many({})

    # Load director config
    director_config = toml.load("prompts.toml")

    # Setup YouTube chat listener
    if args.local_theme:
        db["submission_topics"].insert_one(
            {
                "theme": args.local_theme,
                "requested_by": "admin",
                "status": StatusCodes.ADDED,
            }
        )
    else:
        chat = pytchat.create(os.environ.get("STREAM_ID"))

    while True:
        # Poll chat for new topic submissions
        if not args.local_theme and chat.is_alive():
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
            q_stories = q_stories_list[q_stories_current]
            q_stories_current = (q_stories_current + 1) % args.rq_count

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
                    "job_id": job,
                }
            )

        # Check status of jobs
        finished_jobs = []

        for topic_job in topics_jobs:
            job = topic_job["job_id"]

            match job.get_status():
                case JobStatus.FINISHED:
                    job_result = job.result

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
                    finished_jobs.append(topic_job)

                case _:
                    pass

        # Remove finished jobs
        for job in finished_jobs:
            topics_jobs.remove(job)

            # Remove from submission topics
            db["submission_topics"].delete_one({"_id": job["_id"]})
