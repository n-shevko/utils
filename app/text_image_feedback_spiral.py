import os
import json
import requests
import time
from datetime import datetime
from openai import OpenAI
from app.models import Config

current_directory = os.path.dirname(os.path.abspath(__file__))


def load_config():
    with open(os.path.join(current_directory, 'config.json'), 'r') as f:
        return json.loads(f.read())


def write_config(config):
    with open(os.path.join(current_directory, 'config.json'), 'w') as f:
        f.write(json.dumps(config, indent=2))


def run2():
    now = datetime.now()
    now = now.strftime("%Y_%m_%d_%H_%M_%S")
    out_folder = os.path.join(current_directory, 'out', now)
    os.makedirs(out_folder)

    config = load_config()
    client = OpenAI(api_key=config['chatgpt_api_key'])
    dall_e_settings = config['dall_e_settings']
    chatgpt_settings = config['chatgpt_settings']

    with open(os.path.join(out_folder, f"dalle_request.txt"), 'w') as f:
        f.write(dall_e_settings['prompt'])

    response = client.images.generate(**dall_e_settings)
    url = response.data[0].url
    response = requests.get(url)
    extension = url.split('?')[0].split('.')[-1]
    with open(os.path.join(out_folder, f"dalle_response.{extension}"), "wb") as file:
        file.write(response.content)

    with open(os.path.join(out_folder, f"chatgpt_request.txt"), 'w') as file:
        file.write(config['chatgpt_prompt'])

    chatgpt_settings['model'] = "gpt-4-vision-preview"
    chatgpt_settings['messages'] = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": config['chatgpt_prompt']
                },
                {
                    "type": "image_url",
                    "image_url": {"url": url},
                },
            ],
        }
    ]
    response = client.chat.completions.create(**chatgpt_settings)

    while response.choices[0].finish_reason == 'null':
        time.sleep(1)

    response_path = os.path.join(out_folder, f"chatgpt_response.txt")
    if response.choices[0].finish_reason == 'length':
        out = "Failed: finish_reason == 'length'"
        with open(response_path, 'w') as f:
            f.write(out)
    elif response.choices[0].finish_reason == 'stop':
        out = response.choices[0].message.content
        with open(response_path, 'w') as f:
            f.write(out)
        new_prompt = f"{dall_e_settings['prompt']}\n\n{out}"
        config = load_config()
        config['dall_e_settings']['prompt'] = new_prompt
        write_config(config)
    else:
        out = f"Failed: finish_reason = '{response.choices[0].finish_reason}'\nResponse:{response.choices[0].message.content}"
        with open(response_path, 'w') as f:
            f.write(out)


class Worker:
    def update_config(self, params):
        Config.objects.all().update(**params['config'])