import os
import shlex
import re
import json

import asyncio
import aiohttp
import tiktoken

from uuid import uuid4
from datetime import datetime

from django.conf import settings

from app.utils import get_config, get, update
from app.claude import estimate_cost_claude, run_claude2, slpit_by_chunks
from app import margin_revisions_acceptor


def text_only_path(path):
    tmp, ext = os.path.splitext(path)
    folder = os.path.dirname(tmp)
    filename = os.path.basename(tmp)
    return os.path.join(folder, filename + '_text_only' + ext)


def get_text_only(path):
    with open(path, 'r') as f:
        text = f.read()
    result = re.split(r'\[[\d:.]+\s*-->\s*[\d:.]+\]', text)
    result = ''.join(result)
    for item in ['[MUSIC]', '[BLANK_AUDIO]', '>>', '\n']:
        result = result.replace(item, '')
    result = result.strip()
    result = re.sub(r'\s+', ' ', result)
    with open(text_only_path(path), 'w') as f:
        f.write(result)


async def get_tokens_for_request():
    percent_of_max_tokens_to_use_for_response = int(await get('percent_of_max_tokens_to_use_for_response'))
    tokens_for_request_and_response = 8192
    p = percent_of_max_tokens_to_use_for_response / 100
    return int(tokens_for_request_and_response * (1 - p))


class Worker(margin_revisions_acceptor.Worker):
    async def run_chatgpt(self, params):
        if not params['answer']:
            return

        selected_video = await get('selected_video')
        tmp, _ = os.path.splitext(selected_video)
        folder_path, file_name = os.path.split(tmp)
        formatted_datetime = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        with open(os.path.join(folder_path, file_name + '_text_only.txt'), 'r') as file:
            text = file.read()

        config = await get_config()
        out_file = os.path.join(folder_path, file_name + '_out_' + formatted_datetime + '.txt')
        await update('script_cleaner_last_out_file', out_file)

        task_id = str(uuid4())
        await self.send_msg({
            'fn': 'update',
            'value': {
                'state.script_cleaner_last_out_file': out_file,
                'taskId': task_id
            }
        })

        chunk_size = await self.get_chunk_size()
        delimeter = params['delimeter']
        _, chunks = slpit_by_chunks(text, delimeter, chunk_size, 'gpt-4')
        headers = {
            'Authorization': f'Bearer {config["chatgpt_api_key"]}',
            'Content-Type': 'application/json'
        }
        script_cleaner_prompt = await get('script_cleaner_prompt_not_whole_context')
        limit_reached_times = 0
        for idx, chunk in enumerate(chunks):
            tmp = script_cleaner_prompt.replace('{chunk}', chunk)
            payload = {
                "model": "gpt-4",
                "messages": [
                    {"role": "user", "content": tmp}
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
                            "Api responded with not 200 status. Try again later",
                            callbacks=['unlockRun']
                        )
                        return

            with open(out_file, 'a') as f:
                f.write(response['choices'][0]['message']['content'])

            with open(out_file, 'r') as file:
                content = file.read()

            await update('script_cleaner_last_answer_gpt', content)
            await self.send_msg({
                'fn': 'update',
                'value': {
                    'state.script_cleaner_last_answer_gpt': content,
                    'progress': round(((idx + 1) / len(chunks)) * 100)
                }
            })

            if response['choices'][0]['finish_reason'] == 'length':
                limit_reached_times += 1

            if (await get(f"stop_{task_id}")) == '1':
                break

        extra = ''
        if limit_reached_times > 0:
            extra = f'''<br><br>When the model generated answers for {limit_reached_times} chunks it wanted to generate bigger answer
             but the size of output tokens limited it.<br> To avoid such situations you can increase 'Percent of LLM context to use for response' parameter value'''

        await self.notify(f"Done. Result is in file {out_file}{extra}", callbacks=['unlockRun'])

    async def get_chunk_size(self):
        encoding = tiktoken.encoding_for_model("gpt-4")
        chunk_size = await get_tokens_for_request()
        script_cleaner_prompt = await get('script_cleaner_prompt_not_whole_context')
        chunk_size -= len(encoding.encode(script_cleaner_prompt))
        return chunk_size

    async def estimate_cost_gpt(self, text):
        encoding = tiktoken.encoding_for_model("gpt-4")

        chunk_size = await self.get_chunk_size()
        delimeter = '.'
        flag, chunks = slpit_by_chunks(text, delimeter, chunk_size, 'gpt-4')
        if flag != 'ok':
            delimeter = ' '
            flag, chunks = slpit_by_chunks(text, delimeter, chunk_size, 'gpt-4')

        if flag != 'ok':
            await self.notify("Can't estimate price", callbacks=['unlockRun'])
            return

        input_tokens = 0
        out_tokens = 0
        script_cleaner_prompt = await get('script_cleaner_prompt_not_whole_context')
        for chunk in chunks:
            chunk_in_tokens = len(encoding.encode(chunk))
            input_tokens += chunk_in_tokens + len(encoding.encode(script_cleaner_prompt))
            out_tokens += chunk_in_tokens

        cost = round(((input_tokens / 1000) * 0.03) + ((out_tokens / 1000) * 0.06), 2)
        await self.send_msg(
            {
                'fn': 'update',
                'value': {
                    'dialogTitle': 'Cost estimation',
                    'msg': f"Processing by ChatGPT will use <br>{input_tokens} input tokens<br>{out_tokens} output tokens<br>total cost approximately {cost} $<br><br>Dou you want to continue?",
                    'dialog': 'yes_no_dialog',
                    'delimeter': delimeter,
                    'dialogCallback': 'runChatgpt'
                },
                'callbacks': ['initModal']
            }
        )

    async def script_cleaner_run(self, _):
        model = await get('script_cleaner_model')
        config = await get_config()
        if model == 'chat_gpt':
            if config["chatgpt_api_key"].strip() == '':
                await self.notify(
                    "Please fill in 'OpenAI api key' on 'Settings' tab",
                    callbacks=['unlockRun']
                )
                return
        elif model == 'claude_3':
            if config["claude_api_key"].strip() == '':
                await self.notify(
                    "Please fill in 'Claude api key' on 'Settings' tab",
                    callbacks=['unlockRun']
                )
                return

        selected_video = await get('selected_video')
        folder_path, file_name = os.path.split(selected_video)

        base_name, _ = os.path.splitext(file_name)
        out_file = os.path.join(folder_path, base_name + '.wav')
        wav_exists = os.path.exists(out_file)
        use_existing_files = await get('use_existing_files')
        if not wav_exists or use_existing_files != '1':
            await self.send_msg({
                'fn': 'update',
                'value': {
                    'progress': 5,
                    'progressMsg': 'Extracting audio from video'
                }
            })
            process = await asyncio.create_subprocess_shell(
                f"ffmpeg -i {shlex.quote(selected_video)} -ar 16000 -ac 1 -c:a pcm_s16le -y {shlex.quote(out_file)}"
            )
            await process.communicate()
            if process.returncode != 0:
                await self.notify('Audio extraction failed', callbacks=['unlockRun'])
                return

        await self.send_msg({
            'fn': 'update',
            'value': {
                'progress': 10
            }
        })

        txt_file_path = os.path.join(folder_path, base_name + '.txt')
        txt_exists = os.path.exists(txt_file_path)
        if not txt_exists or use_existing_files != '1':
            whisper = os.path.join(settings.WHISPER, 'main')
            model = os.path.join(settings.WHISPER, 'models/ggml-base.en.bin')
            process = await asyncio.create_subprocess_shell(
                f"{whisper} -m {model} -t {os.cpu_count() - 1} -f {shlex.quote(out_file)} > {shlex.quote(txt_file_path)}"
            )
            await process.communicate()
            if process.returncode != 0:
                await self.notify('Extracting text from audio failed', callbacks=['unlockRun'])
                return
            else:
                await self.send_msg({
                    'fn': 'update',
                    'value': {
                        'progress': 15
                    }
                })

        if not os.path.exists(text_only_path(txt_file_path)):
            get_text_only(txt_file_path)

        with open(text_only_path(txt_file_path), 'r') as file:
            text = file.read()
        script_cleaner_model = await get('script_cleaner_model')
        if script_cleaner_model == 'chat_gpt':
            await self.estimate_cost_gpt(text)
        else:
            await estimate_cost_claude(self, text)

    async def run_claude(self, params):
        await run_claude2(self, params)