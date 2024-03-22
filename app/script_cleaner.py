import os
import shlex
import re

import asyncio
from uuid import uuid4

from datetime import datetime

import tiktoken
from openai import OpenAI

from django.conf import settings


from app.utils import Common, get_config, db, get, update
from app.models import Config

solution = "You can solve this problem by increasing 'Percent of LLM context to use for response'"


def text_only_path(path):
    tmp, ext = os.path.splitext(path)
    folder = os.path.dirname(tmp)
    filename = os.path.basename(tmp)
    return os.path.join(folder, filename + '_text_only' + ext)


async def get_text_only(path):
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


async def estimate_cost(text):
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
        return {
            'fn': 'yes_no_dialog',
            'title': 'Cost estimation',
            'msg': f"Processing by ChatGPT will use <br>{input_tokens} input tokens<br>{out_tokens} output tokens<br>total cost approximately {cost} $<br><br>Dou you want to continue?",
            'response': {
                'fn': 'run_chatgpt',
                'args': delimeter
            }
        }
    else:
        return {
            'fn': 'notify_dialog',
            'title': 'Notification',
            'msg': f"Can't create request for an sentence. The sentence is too big.<br>" +
               "You may solve this problem by reducing 'Percent of LLM context to use for response'. If it doesn't help then mail to nicksheuko@gmail.com"
        }


async def get_tokens_for_request():
    percent_of_max_tokens_to_use_for_response = int(await get('percent_of_max_tokens_to_use_for_response'))
    tokens_for_request_and_response = 8192
    p = percent_of_max_tokens_to_use_for_response / 100
    return int(tokens_for_request_and_response * (1 - p))


async def call_chatgpt(config, client, user_mesage, out_file, tokens_for_response):
    # response = client.chat.completions.create(
    #     model="gpt-4",
    #     messages=[
    #         {
    #             "role": "system",
    #             "content": config.script_cleaner_prompt
    #         },
    #         {
    #             "role": "user",
    #             "content": user_mesage
    #         }
    #     ],
    #     temperature=config.chat_gpt_temperature,
    #     max_tokens=tokens_for_response,  # desired response size
    #     top_p=config.chat_gpt_top_p,
    #     frequency_penalty=config.chat_gpt_frequency_penalty,
    #     presence_penalty=config.chat_gpt_presence_penalty
    # )
    # while response.choices[0].finish_reason == 'null':
    #     time.sleep(1)
    #
    # if response.choices[0].finish_reason == 'length':
    #     #notify("finish_reason == 'length'\n" + solution)
    #     return True
    #
    # if response.choices[0].finish_reason == 'stop':
    #     out = response.choices[0].message.content
    # else:
    #     out = f"\n\n\nUnusual finish_reason = '{response.choices[0].finish_reason}' for Reqest:\n {system_message}\n\n{user_mesage}\n\nResponse:{response.choices[0].message.content}\n\n\n"
    out = 'abc'
    await asyncio.sleep(0.5)
    with open(out_file, 'a') as f:
        f.write(out)
    return False


class Worker(Common):
    async def run_chatgpt(self, params):
        if not params['answer']:
            return

        selected_video = await get('selected_video')
        tmp, _ = os.path.splitext(selected_video)
        folder_path, file_name = os.path.split(tmp)
        formatted_datetime = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        with open(os.path.join(folder_path, file_name + '_text_only.txt'), 'r') as file:
            text = file.read() * 1000

        delimeter = params['args']
        config = await get_config()
        client = OpenAI(api_key=config['chatgpt_api_key'])
        offset = 0
        sentences = text.split(delimeter)
        # sentences = sentences[0:2]
        stop = False
        out_file = os.path.join(folder_path, file_name + '_out_' + formatted_datetime + '.txt')
        await update('script_cleaner_last_out_file', out_file)
        encoding = tiktoken.encoding_for_model("gpt-4")
        tokens_for_request = await get_tokens_for_request()
        tokens_for_request_and_response = 8192
        task_id = str(uuid4())
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
            stop = await call_chatgpt(config, client, request, out_file, tokens_for_response)
            with open(out_file, 'r') as file:
                content = file.read()
            await update('script_cleaner_last_answer_gpt', content)
            await self.send_msg({
                'fn': 'update_gpt_answer',
                'answer': content,
                'task_id': task_id,
                'out_file': out_file,
                'progress': ((offset + 1) / len(sentences)) * 100
            })

            if stop:
                break

            if (await get(f"stop_{task_id}")) == '1':
                break
        if stop:
            msg = f"Not complete result in file {out_file}<br>{solution}"
        else:
            msg = f"Done. Result in file {out_file}"
        await self.send_msg({
            'fn': 'notify_dialog',
            'title': 'Notification',
            'callback': 'unlockRun',
            'msg': msg
        })

    async def script_cleaner_run(self, _):
        selected_video = await get('selected_video')
        folder_path, file_name = os.path.split(selected_video)

        base_name, _ = os.path.splitext(file_name)
        out_file = os.path.join(folder_path, base_name + '.wav')
        wav_exists = os.path.exists(out_file)
        use_existing_files = await get('use_existing_files')
        if not wav_exists or use_existing_files != '1':
            # progressbar['value'] = 5
            response = os.system(f"ffmpeg -i {shlex.quote(selected_video)} -ar 16000 -ac 1 -c:a pcm_s16le -y {shlex.quote(out_file)}")
            if response != 0:
                # notify("Audio extraction failed")
                return
        #progressbar['value'] = 10

        txt_file_path = os.path.join(folder_path, base_name + '.txt')
        txt_exists = os.path.exists(txt_file_path)
        if not txt_exists or use_existing_files != '1':
            whisper = os.path.join(settings.WHISPER, 'main')
            model = os.path.join(settings.WHISPER, 'models/ggml-base.en.bin')
            response = os.system(f"{whisper} -m {model} -t {os.cpu_count() - 1} -f {shlex.quote(out_file)} > {shlex.quote(txt_file_path)}")

            if response != 0:
                #notify("Extracting text from audio failed")
                return
            else:
                get_text_only(txt_file_path)

        with open(text_only_path(txt_file_path), 'r') as file:
            await self.send_msg(await estimate_cost(file.read()))