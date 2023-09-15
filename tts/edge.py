from dotenv import load_dotenv
from pymongo import MongoClient

import asyncio
import edge_tts
import os

load_dotenv()

mongo_client = MongoClient(os.environ.get("MONGO_URI"))
mongo_client.server_info()

db = mongo_client["ai-galileo"]

voice_actor = "ru-RU-DmitryNeural"


async def generate(tetx, voice, output_file):
    communicate = edge_tts.Communicate(tetx, voice, rate="+12%", pitch="+20Hz")
    await communicate.save(output_file)


# Retrieve all stories
stories = db["stories"].find({})

if __name__ == "__main__":
    loop = asyncio.get_event_loop_policy().get_event_loop()
    try:
        for story in stories[:1]:
            for sequence in ["pre_story", "story", "post_story"]:
                for idx, line in enumerate(story[sequence]):
                    match line["type"]:
                        case "text":
                            text = line["text"]
                            if not text:
                                continue

                            loop.run_until_complete(
                                generate(
                                    line["text"],
                                    voice_actor,
                                    f"out/{sequence}{idx}.mp3",
                                )
                            )

                        case _:
                            pass
    finally:
        loop.close()
