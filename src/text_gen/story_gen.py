from claude_api import Client
from loguru import logger

from utils import toml_interpolate

import os
import re


class ChatContext:
    """Context manager for Claude API. Creates a new chat and deletes it when the context exits."""

    def __init__(self):
        cookie = os.environ.get("COOKIE")

        if not cookie:
            raise Exception("No COOKIE env variable provided.")

        self.claude_client = Client(cookie)
        self.chat_id = None

    def __enter__(self):
        self.chat_id = self.claude_client.create_new_chat()["uuid"]
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # self.claude_client.delete_conversation(self.chat_id)
        self.chat_id = None


def generate_episode(config: dict, theme: str) -> dict:
    """Generate an episode from a theme, which includes a story, intro, and outro."""

    response = {"theme": theme}

    # Form prompts by interpolating TOML strings
    prompts_items = ["story", "story_intro", "story_outro"]
    prompts = {}
    for item in prompts_items:
        prompts[item] = toml_interpolate(
            config["prompts"][item],
            [response, config],
        )

    with ChatContext() as ctx:
        for item in prompts_items:
            response[item] = parse_story(
                ctx.claude_client.send_message(
                    prompts[item],
                    ctx.chat_id,
                    timeout=600,
                )
            )

            logger.info(f"Succesfully generated {item} for theme {theme}.")

    return response


def generate_episode_testonly(config: dict, theme: str) -> dict:
    import time

    time.sleep(5)

    return {"theme": theme}


def parse_story(story_text: str) -> list:
    """Parse story text into a list of phrases and actions."""
    phrases = story_text.split("\n\n")  # Extract phrases

    # Remove leading and trailing whitespace
    phrases = [phrase.strip() for phrase in phrases]
    phrases = [p for p in phrases if p]

    script = []
    for phrase in phrases:
        # Extract actions from phrase
        actions = re.findall(r"\((.*?)\)", phrase)

        # Remove actions from phrase
        phrase = re.sub(r"\(.*?\)", "", phrase).strip()

        if phrase:
            script.append(
                {
                    "type": "text",
                    "text": phrase,
                    "voice": None,
                }
            )

        for action in actions:
            script.append(
                {
                    "type": "action",
                    "action": action,
                }
            )

    return script
