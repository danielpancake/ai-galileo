from claude_api import Client
from dotenv import load_dotenv
from loguru import logger
from typing import List, Tuple, Dict, Any

import os
import re
import toml

load_dotenv()


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
    promps_section = config["prompts"]

    config["theme"] = theme

    prompt_story = toml_interpolate(promps_section["story_prompt"], config)
    prompt_pre_story = toml_interpolate(promps_section["pre_story_prompt"], config)
    prompt_post_story = toml_interpolate(promps_section["post_story_prompt"], config)

    r = {
        "theme": theme,
    }

    with StoryContext() as ctx:
        logger.info(f"Story ID: {ctx.story_id}")
        r["story"] = ctx.claude_client.send_message(
            prompt_story, ctx.story_id, timeout=600
        )
        logger.info("Generated story")
        r["pre_story"] = ctx.claude_client.send_message(
            prompt_pre_story, ctx.story_id, timeout=600
        )
        logger.info("Generated pre_story")
        r["post_story"] = ctx.claude_client.send_message(
            prompt_post_story, ctx.story_id, timeout=600
        )
        logger.info("Generated post_story")

    return r


config = toml.load("director.toml")

print(generate_full_story(config, "Как работают нейронные сети?"))


#
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
