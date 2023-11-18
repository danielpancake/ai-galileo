from dotenv import load_dotenv
from pymongo import MongoClient

import asyncio
import edge_tts
import os

load_dotenv()

mongo_client = MongoClient(os.environ.get("MONGO_URI"))
mongo_client.server_info()

db = mongo_client["ai-galileo"]

voice_actor = "ru-RU-SvetlanaNeural"


async def generate(tetx, voice, output_file):
    communicate = edge_tts.Communicate(tetx, voice, rate="+15%", pitch="-18Hz")
    await communicate.save(output_file)


# Retrieve all stories
stories = db["stories"].find({})

if __name__ == "__main__":
    loop = asyncio.get_event_loop_policy().get_event_loop()
    try:
        for story in stories:
            story_id = story["_id"]

            # Create output directory
            os.makedirs(f"out/{story_id}", exist_ok=True)

            for sequence in ["pre_story", "story", "post_story"]:
                idx = 0
                for line in story[sequence]:
                    match line["type"]:
                        case "text":
                            text = line["text"]
                            if not text:
                                continue

                            loop.run_until_complete(
                                generate(
                                    line["text"],
                                    voice_actor,
                                    f"out/{story_id}/{sequence}{idx}.mp3",
                                )
                            )

                            idx += 1

                        case _:
                            pass
    finally:
        loop.close()
