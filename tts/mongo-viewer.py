from dotenv import load_dotenv
from pymongo import MongoClient

import os

load_dotenv()

mongo_client = MongoClient(os.environ.get("MONGO_URI"))
mongo_client.server_info()

db = mongo_client["ai-galileo"]

# Retrieve all stories
stories = db["stories"].find({})

if __name__ == "__main__":
    for story in stories[:1]:
        print(f"=== Current story: {story['theme']} ===")
        for sequence in ["pre_story", "story", "post_story"]:
            print(f"=== Current sequence: {sequence} ===")
            for idx, line in enumerate(story[sequence]):
                match line["type"]:
                    case "text":
                        print(line["text"])

                    case "action":
                        print(f"* {line['action']} *")

            print("")
