from claude_api import Client
from dotenv import load_dotenv
from typing import List, Tuple, Dict, Any

import os
import re
import toml


class StoryContext:
    def __init__(self):
        self.claude_client = Client(os.environ.get("COOKIE"))
        self.story_id = None

    def __enter__(self):
        story_generator = self.claude_client.create_new_chat()
        self.story_id = story_generator["uuid"]
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.claude_client.delete_conversation(self.story_id)
        self.story_id = None


def toml_interpolate(string: str, config: dict) -> str:
    """Interpolate TOML string with config variables."""
    interpolation_candidates = re.findall(r"\%(.+?)\%", string)

    for candidate in interpolation_candidates:
        path = candidate.split("/")
        value = config

        for key in path:
            if key in value:
                value = value[key]
            else:
                value = None
                break

        if value:
            string = string.replace(f"%{candidate}%", value)

    return string


def parse_story(story_text: str) -> list:
    """Parse story text into a list of phrases and actions."""
    phrases = story_text.split("\n\n")  # extract phrases

    # remove empty lines
    phrases = [phrase.strip() for phrase in phrases]
    phrases = [p for p in phrases if p]

    script = []

    for phrase in phrases:
        # extract actions from phrase
        actions = re.findall(r"\((.*?)\)", phrase)

        # remove actions from phrase
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


def generate_full_story(config, theme: str) -> dict:
    pass


# load_dotenv()

# config = toml.load("director.toml")
# claude_api = Client(os.environ.get("COOKIE"))

# theme = "Зачем нужны шишки"

# pushnoy_actions = config["actions"]["pushnoy_actions"]

# episode_generator = claude_api.create_new_chat()
# episode_id = episode_generator["uuid"]

# prompt = config["prompts"]["base_prompt"]
# prompt = prompt.replace("*theme_here*", theme)
# prompt = prompt.replace("*pushnoy_actions*", pushnoy_actions)

# response = claude_api.send_message(prompt, episode_id, timeout=600)
# print(response)

# claude_api.delete_conversation(episode_id)


# def generate_story(config, theme: str):
#   prompt = theme

#   claude_client = Client(os.environ.get("COOKIE"))

#   story_generator = claude_client.create_new_chat()
#   story_id = story_generator["uuid"]

#   response = claude_client.send_message(prompt, story_id, timeout=600)
