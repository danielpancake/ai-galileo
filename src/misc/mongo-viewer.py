from dotenv import load_dotenv
from pymongo import MongoClient

import os

load_dotenv()

if __name__ == "__main__":
    mongo_client = MongoClient(os.getenv("MONGO_URI"))
    mongo_client.server_info()

    stories = mongo_client["ai_galileo"]["stories"]

    # Retrieve all stories
    fetched_stories = stories.find({})

    for story in fetched_stories:
        print(f"=== Current story: {story['theme']} with id {story['_id']} ===")
        for sequence_type in ["story_intro", "story", "story_outro"]:
            print(f"=== Current sequence: {sequence_type} ===")
            for index, line in enumerate(story[sequence_type]):
                match line["type"]:
                    case "text":
                        print(line["text"])
                        print(f"Voice: {line['voice']}")

                    case "action":
                        print(f"* {line['action']} *")

            print("")
