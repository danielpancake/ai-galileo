from bson.objectid import ObjectId
from dotenv import load_dotenv
from os import listdir
from os.path import isfile, join
from pymongo import MongoClient

import os

load_dotenv()

mongo_client = MongoClient(os.environ.get("MONGO_URI"))
mongo_client.server_info()

db = mongo_client["ai-galileo"]

story_ids = [f for f in listdir("rvc-out") if not isfile(join("out", f))]

absolute_path = os.path.abspath(os.getcwd())

for story_id in story_ids:
    story = db["stories"].find_one({"_id": ObjectId(story_id)})
    for sequence in ["pre_story", "story", "post_story"]:
        # Add voice path to story
        idx = 0
        for line in story[sequence]:
            if line["type"] == "text":
                story[sequence][idx][
                    "voice"
                ] = f"{absolute_path}/rvc-out/{story_id}/{sequence}{idx}.wav"
            idx += 1

    # Update the story
    db["stories"].update_one({"_id": ObjectId(story_id)}, {"$set": story})
