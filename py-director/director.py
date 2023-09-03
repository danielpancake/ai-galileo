from claude_api import Client
from loguru import logger
from utils import toml_interpolate

import os
import re


class StoryContext:
    def __init__(self):
        cookie = os.environ.get("COOKIE")

        if not cookie:
            raise Exception("No COOKIE env variable provided.")

        self.claude_client = Client(cookie)
        self.story_id = None

    def __enter__(self):
        story_generator = self.claude_client.create_new_chat()
        self.story_id = story_generator["uuid"]
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.claude_client.delete_conversation(self.story_id)
        self.story_id = None


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


def generate_full_story(config: dict, theme: str) -> dict:
    """Generate a full story from a theme, which includes an intro, story, and outro."""

    prompts_items = ["story", "pre_story", "post_story"]

    response = {
        "theme": theme,
    }

    # Form prompts by interpolating TOML strings
    prompts = {}
    for item in prompts_items:
        prompts[item] = toml_interpolate(config["prompts"][item], [response, config])

    with StoryContext() as ctx:
        logger.info(f"Story ID: {ctx.story_id}")

        for item in prompts_items:
            response[item] = ctx.claude_client.send_message(
                prompts[item], ctx.story_id, timeout=600
            )

            response[item] = parse_story(response[item])

            logger.info(f"Generated {item}")

    return response
