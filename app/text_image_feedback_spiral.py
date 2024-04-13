import os

import aiohttp
import json
import uuid

from django.conf import settings

from app import script_cleaner

from app.utils import db, get_config, get, update
from app.models import Step

from channels.db import database_sync_to_async


@database_sync_to_async
def create_step():
    step = Step()
    step.save()
    return step.id


@database_sync_to_async
def get_last_steps(n):
    urls = []
    for step in Step.objects.order_by('-created_at')[:n]:
        urls.append(step.dalle_response.url)
    return urls


class Worker(script_cleaner.Worker):
    async def get_feedback_spiral_context(self, _):
        config = await get_config()
        last_steps = await get_last_steps(config["dall_e_show_last_images"])
        await self.send_msg({
            'fn': 'update',
            'value': {
                'last_steps': last_steps,
            }
        })

    async def step(self, _):
        config = await get_config()
        if config["chatgpt_api_key"].strip() == '':
            await self.notify(
                "Please fill in 'OpenAI api key' on 'Settings' tab",
                callbacks=['unlockRun']
            )
            return

        url = 'https://api.openai.com/v1/images/generations'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {config["chatgpt_api_key"]}'
        }
        original_prompt = await get('dalle_request')
        data = {
            'model': 'dall-e-3',
            'prompt': original_prompt,
            'n': 1,
            'size': config['dall_e_size'],
            'quality': config['dall_e_quality'],
            'style': config['dall_e_style'],
            'response_format': 'url'
        }
        await self.send_msg({
            'fn': 'update',
            'value': {
                'progress': 10
            }
        })
        async with aiohttp.ClientSession(timeout=None) as session:
            async with session.post(url, json=data, headers=headers, timeout=None) as response:
                response_json = await response.json()

        await self.send_msg({
            'fn': 'update',
            'value': {
                'progress': 50
            }
        })

        unique_id = str(uuid.uuid4())
        file_name = f'{unique_id}.png'
        path = os.path.join(settings.MEDIA_ROOT, file_name)

        url = response_json['data'][0]['url']
        async with aiohttp.ClientSession(timeout=None) as session:
            async with session.get(url, timeout=None) as response:
                if response.status == 200:
                    with open(path, 'wb') as file:
                        file.write(await response.read())
                else:
                    await self.notify(
                        "Can't download image from dalle. Try again later",
                        callbacks=['unlockRun']
                    )
                    return

        revised_prompt = response_json['data'][0]['revised_prompt']
        id = await create_step()
        suggest_changes_request = await get('suggest_changes_request')
        async with db() as c:
            await c.execute(
                'UPDATE app_step SET dalle_request = %s, revised_prompt = %s, dalle_response=%s, suggest_changes_request=%s WHERE id=%s',
                (original_prompt, revised_prompt, file_name, suggest_changes_request, id)
            )

        await self.send_msg({
            'fn': 'update',
            'value': {
                'progress': 75,
                'last_steps': await get_last_steps(config["dall_e_show_last_images"])
            }
        })

        # https://platform.openai.com/docs/api-reference/images
        payload = {
            "model": "gpt-4-turbo",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            'type': 'text',
                            'text': suggest_changes_request
                        },
                        {
                            'type': 'image_url',
                            'image_url': {
                                'url': url
                            }
                        }
                    ]
                }
            ],
            "temperature": config['chat_gpt_temperature'],
            "top_p": config['chat_gpt_top_p'],
            "frequency_penalty": config['chat_gpt_frequency_penalty'],
            "presence_penalty": config['chat_gpt_presence_penalty']
        }

        async with aiohttp.ClientSession(timeout=None) as session:
            async with session.post('https://api.openai.com/v1/chat/completions', headers=headers,
                                    data=json.dumps(payload), timeout=None) as response:
                if response.status == 200:
                    response = await response.json()
                else:
                    await self.notify(
                        "Chat Gpt api responded with not 200 status. Try again later",
                        callbacks=['unlockRun']
                    )
                    return

        await self.send_msg({
            'fn': 'update',
            'value': {
                'progress': 100
            }
        })

        suggest_changes_response = response['choices'][0]['message']['content']
        async with db() as c:
            await c.execute(
                'UPDATE app_step SET suggest_changes_response=%s WHERE id=%s',
                (suggest_changes_response, id)
            )

        new_create_image_prompt = f'{original_prompt}\n{suggest_changes_response}'
        await update('dalle_request', new_create_image_prompt)
        await self.send_msg({
            'fn': 'update',
            'value': {
                'state.dalle_request': new_create_image_prompt
            },
            'callbacks': ['setInprogressFalse']
        })
