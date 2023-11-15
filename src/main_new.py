from bson import ObjectId
from dotenv import load_dotenv
from loguru import logger
from main_ui import AppUI
from pymongo import MongoClient, errors
from rq_conductor import RQConductor
from statuses import StatusCodes

import argparse
import os


QUEUE_STORIES_BASENAME = "stories"

load_dotenv()
logger.add("logs/main.log")


def setup_args():
    """Setup command line arguments."""
    parser = argparse.ArgumentParser(
        prog="ai-galileo",
        description="AI Galileo is a chatbot that generates stories based on user-submitted topics.",
    )
    parser.add_argument("--clear", help="Clear the database", action="store_true")
    parser.add_argument("--rq-start", help="Run RQ workers", action="store_true")
    parser.add_argument(
        "--rq-count", help="Number of RQ workers for stories queue", type=int, default=3
    )
    parser.add_argument(
        "--rq-piper-count", help="Number of RQ workers piper tts", type=int, default=3
    )
    parser.add_argument(
        "--yt", help="Start the YouTube chat listener. Requires stream ID", type=str
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = setup_args()

    # Setup MongoDB
    try:
        mongo_client = MongoClient(os.getenv("MONGO_URI"))
        mongo_client.server_info()
    except errors.ServerSelectionTimeoutError as err:
        logger.error(err)
        exit(1)

    logger.info("Connected to MongoDB")

    # The main mongo database has two collections:
    # - `submission_topics`: stores the topics that have been submitted
    # - `stories`: stores the stories that have been processed
    db = mongo_client["ai_galileo"]

    # The schema for `submission_topics` is:
    # {
    #     "_id": ObjectId,
    #     "theme": str,
    #     "status": int,
    #     "requested_by": str,
    #     "requested_at": datetime,
    # }
    submission_topics = db["submission_topics"]

    # The schema for `stories` is:
    # {
    #     "_id": ObjectId,
    #     "theme": str,
    #     "pre_story": list[dict],
    #     "story": list[dict],
    #     "post_story": list[dict],
    #     "requested_by": str,
    #     "requested_at": datetime,
    # }
    stories = db["stories"]
    stories_rq_conductor = RQConductor(
        QUEUE_STORIES_BASENAME, args.rq_count, args.rq_start
    )

    # Clear the database if requested
    if args.clear:
        delete_all = input(
            "Are you sure you want to clear the database? This action cannot be undone. [y/N] "
        )

        if delete_all.lower() == "y":
            submission_topics.delete_many({})
            stories.delete_many({})
            logger.info("Cleared the database")

    # Setup the app UI
    if args.yt:
        UI = AppUI(submission_topics, yt_stream_id=args.yt)
    else:
        UI = AppUI(submission_topics)

    while True:
        # Process newly added topics
        for topic in submission_topics.find({"status": StatusCodes.ADDED}):
            stories_rq_conductor.enqueue_job(
                print,
                args=[topic["theme"]],
                job_id=str(topic["_id"]),
                job_timeout=3600,
            )

            # Update status
            submission_topics.update_one(
                {"_id": topic["_id"]}, {"$set": {"status": StatusCodes.QUEUED}}
            )

        stories_rq_conductor.update(
            lambda _id, result: submission_topics.update_one(
                {"_id": ObjectId(_id)}, {"$set": {"status": StatusCodes.FINISHED}}
            )
        )

        UI.update()
