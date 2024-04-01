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
from app import margin_revisions_acceptor


solution = "You can solve this problem by increasing 'Percent of LLM context to use for response'"


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


def try_split(delimiter, text, tokens_for_request, encoding, script_cleaner_prompt):
    sentences = text.split(delimiter)
    offset = 0
    input_tokens = 0
    out_tokens = 0
    request_is_too_big = False
    while offset < len(sentences):
        request = []
        while offset < len(sentences):
            sentence = sentences[offset]
            tmp = delimiter.join(request + [script_cleaner_prompt, sentence])
            cnt = len(encoding.encode(tmp))
            if cnt <= tokens_for_request:
                request.append(sentence)
                offset += 1
            else:
                break

        if not request and offset < len(sentences):
            request_is_too_big = True
            break

        request = delimiter.join(request)
        request_input_tokens = len(encoding.encode(request + script_cleaner_prompt))
        input_tokens += request_input_tokens
        out_tokens += (8192 - request_input_tokens - 100)
    return request_is_too_big, input_tokens, out_tokens


async def get_tokens_for_request():
    percent_of_max_tokens_to_use_for_response = int(await get('percent_of_max_tokens_to_use_for_response'))
    tokens_for_request_and_response = 8192
    p = percent_of_max_tokens_to_use_for_response / 100
    return int(tokens_for_request_and_response * (1 - p))


class Worker(margin_revisions_acceptor.Worker):
    async def call_chatgpt(self, config, user_message, out_file, tokens_for_response, script_cleaner_prompt):
        headers = {
            'Authorization': f'Bearer {config["chatgpt_api_key"]}',
            'Content-Type': 'application/json'
        }
        payload = {
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": script_cleaner_prompt},
                {"role": "user", "content": user_message}
            ],
            "temperature": config['chat_gpt_temperature'],
            "max_tokens": tokens_for_response,
            "top_p": config['chat_gpt_top_p'],
            "frequency_penalty": config['chat_gpt_frequency_penalty'],
            "presence_penalty": config['chat_gpt_presence_penalty']
        }
        for attempt in range(3):
            async with aiohttp.ClientSession() as session:
                async with session.post('https://api.openai.com/v1/completions', headers=headers,
                                        data=json.dumps(payload)) as response:
                    if response.status == 200:
                        response = await response.json()
                        break
                    else:
                        await self.notify("Failed to fetch response from OpenAI")
                        return True

        if response['choices'][0]['finish_reason'] == 'length':
            await self.notify(f"finish_reason == 'length'<br>{solution}")
            return True
        if response['choices'][0]['finish_reason'] == 'stop':
            with open(out_file, 'a') as f:
                f.write(response['choices'][0]['message']['content'])
            return False
        else:
            await self.notify(f'''Unusual finish_reason = '{response['choices'][0]['finish_reason']}' for Request:
            <br>{script_cleaner_prompt}
            <br>{user_message}
            <br>Response:{response['choices'][0]['message']['content']}''')
            return True

        # out = 'abc'
        # await asyncio.sleep(0.5)
        # with open(out_file, 'a') as f:
        #     f.write(out)
        # return False

    async def run_chatgpt(self, params):
        if not params['answer']:
            return

        selected_video = await get('selected_video')
        tmp, _ = os.path.splitext(selected_video)
        folder_path, file_name = os.path.split(tmp)
        formatted_datetime = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        with open(os.path.join(folder_path, file_name + '_text_only.txt'), 'r') as file:
            text = file.read()# * 1000

        delimeter = params['delimeter']
        config = await get_config()
        if config["chatgpt_api_key"].strip() == '':
            await self.notify("Please fill in 'OpenAI api key' on 'Settings' tab")
            return

        offset = 0
        sentences = text.split(delimeter)
        # sentences = sentences[0:2]
        stop = False

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

        encoding = tiktoken.encoding_for_model("gpt-4")
        tokens_for_request = await get_tokens_for_request()
        tokens_for_request_and_response = 8192

        script_cleaner_prompt = await get('script_cleaner_prompt')
        while offset < len(sentences):
            request = []
            while offset < len(sentences):
                sentence = sentences[offset]
                tmp = delimeter.join(request + [script_cleaner_prompt, sentence])
                cnt = len(encoding.encode(tmp))
                if cnt <= tokens_for_request:
                    request.append(sentence)
                    offset += 1
                else:
                    break

            request = delimeter.join(request)
            tokens_for_response = tokens_for_request_and_response - len(
                encoding.encode(request + script_cleaner_prompt)) - 100
            stop = await self.call_chatgpt(
                config,
                request,
                out_file,
                tokens_for_response,
                script_cleaner_prompt
            )
            with open(out_file, 'r') as file:
                content = file.read()
            await update('script_cleaner_last_answer_gpt', content)
            await self.send_msg({
                'fn': 'update',
                'value': {
                    'state.script_cleaner_last_answer_gpt': content,
                    'progress': round(((offset + 1) / len(sentences)) * 100)
                }
            })

            if stop:
                break

            if (await get(f"stop_{task_id}")) == '1':
                break

        if not stop:
            await self.notify(f"Done. Result in file {out_file}")

    async def estimate_cost(self, text):
        encoding = tiktoken.encoding_for_model("gpt-4")
        tokens_for_request = await get_tokens_for_request()
        script_cleaner_prompt = await get('script_cleaner_prompt')
        point_attempt = try_split('.', text, tokens_for_request, encoding, script_cleaner_prompt)
        space_attempt = try_split(' ', text, tokens_for_request, encoding, script_cleaner_prompt)
        if (not point_attempt[0]) or (not space_attempt[0]):
            if not point_attempt[0]:
                choice = point_attempt
                delimeter = '.'
            elif not space_attempt[0]:
                choice = space_attempt
                delimeter = ' '
            input_tokens = choice[1]
            out_tokens = choice[2]
            cost = round(((input_tokens / 1000) * 0.03) + ((out_tokens / 1000) * 0.06), 1)
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
                    'callback': 'initModal'
                }
            )
        else:
            await self.notify(
                f"Can't create request for an sentence. The sentence is too big.<br>You may solve this problem by reducing 'Percent of LLM context to use for response'. If it doesn't help then mail to nicksheuko@gmail.com"
            )

    async def script_cleaner_run(self, _):
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
                await self.notify('Audio extraction failed')
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
                await self.notify('Extracting text from audio failed')
                return
            else:
                await self.send_msg({
                    'fn': 'update',
                    'value': {
                        'progress': 15
                    }
                })
                get_text_only(txt_file_path)

        with open(text_only_path(txt_file_path), 'r') as file:
            await self.estimate_cost(file.read())