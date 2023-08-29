from claude_api import Client
from dotenv import load_dotenv

import os
import toml

load_dotenv()

config = toml.load("director.toml")
claude_api = Client(os.environ.get("COOKIE"))

theme = "Зачем нужны шишки"

episode_generator = claude_api.create_new_chat()
episode_id = episode_generator["uuid"]

prompt = config["prompts"]["base_prompt"]
prompt = prompt.replace("*theme_here*", theme)

response = claude_api.send_message(prompt, episode_id, timeout=600)
print(response)

claude_api.delete_conversation(episode_id)
