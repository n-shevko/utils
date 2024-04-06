import aiohttp
import tiktoken
import os
import asyncio

from uuid import uuid4
from datetime import datetime

from app.utils import get_config, Common, get, update


async def slpit_by_chunks(text, delimeter):
    claude_max_tokens = int(await get('claude_max_tokens'))
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    sentenses = text.split(delimeter)

    idx = 0
    chunk = []
    chunks = []
    while idx < len(sentenses):
        sentence = sentenses[idx]
        tokens = len(encoding.encode(delimeter.join(chunk + [sentence])))
        if tokens <= claude_max_tokens:
            chunk.append(sentence)
        elif len(encoding.encode(delimeter.join(chunk))) <= claude_max_tokens:
            chunks.append(chunk)
            chunk = [sentence]
        else:
            return 'chunk_is_too_big', None
        idx += 1

    if len(encoding.encode(delimeter.join(chunk))) <= claude_max_tokens:
        if not chunk:
            return 'empty_result', None
        else:
            chunks.append(chunk)
            return 'ok', [delimeter.join(chunk) for chunk in chunks]
    else:
        return 'chunk_is_too_big', None


async def estimate_cost_claude(self: Common, text):
    delimeter = '.'
    flag, chunks = await slpit_by_chunks(text, delimeter)
    if flag != 'ok':
        delimeter = ' '
        flag, chunks = await slpit_by_chunks(text, delimeter)
        if flag != 'ok':
            await self.notify("Can't estimate price")
            return

    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    script_cleaner_prompt = await get('script_cleaner_prompt_claude_3')

    input_context = [script_cleaner_prompt]
    for idx, chunk in enumerate(chunks):
        input_context.append(f'''[START_CHUNK_{idx}]
        {chunk}
[END_CHUNK_{idx}]''')
    input_context = '\n'.join(input_context)
    input_context_tokens = len(encoding.encode(input_context))

    dollars_per_input_token = 15 / 1000000
    dollars_per_output_token = 75 / 1000000
    total_out_tokens = 0
    for chunk in chunks:
        estimated_out_tokens = len(encoding.encode(chunk))
        total_out_tokens += estimated_out_tokens
    input_tokens_price = len(chunks) * input_context_tokens * dollars_per_input_token
    out_tokens_price = total_out_tokens * dollars_per_output_token
    total_price = round(input_tokens_price + out_tokens_price, 2)
    await self.send_msg(
        {
            'fn': 'update',
            'value': {
                'dialogTitle': 'Cost estimation',
                'msg': f"Processing by Claude 3 will cost approximately {total_price} $<br><br>Dou you want to continue?",
                'dialog': 'yes_no_dialog',
                'delimeter': delimeter,
                'dialogCallback': 'runClaude3'
            },
            'callbacks': ['initModal']
        }
    )


async def run_claude2(self: Common, params):
    if not params['answer']:
        return

    selected_video = await get('selected_video')
    tmp, _ = os.path.splitext(selected_video)
    folder_path, file_name = os.path.split(tmp)
    formatted_datetime = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    with open(os.path.join(folder_path, file_name + '_text_only.txt'), 'r') as file:
        text = file.read()

    delimeter = params['delimeter']
    config = await get_config()
    if config["claude_api_key"].strip() == '':
        await self.notify(
            "Please fill in 'Claude api key' on 'Settings' tab",
            callbacks=['unlockRun']
        )
        return

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

    _, chunks = await slpit_by_chunks(text, delimeter)
    input_context = []
    for idx, chunk in enumerate(chunks):
        input_context.append(f'''[START_CHUNK_{idx}]
        {chunk}
        [END_CHUNK_{idx}]''')

    input_context = '\n'.join(input_context)
    script_cleaner_prompt = await get('script_cleaner_prompt_claude_3')
    headers = {
        'content-type': 'application/json',
        'anthropic-version': '2023-06-01',
        'x-api-key': config["claude_api_key"]
    }
    stop = False
    for idx, _ in enumerate(chunks):
        tmp = script_cleaner_prompt.replace('{text}', input_context).replace('{chunk}', str(idx))
        data = {
            "model": "claude-3-opus-20240229",
            "max_tokens": 4096,
            "temperature": config['claude_temperature'],
            "messages": [
                {
                    "role": "user",
                    "content": tmp
                }
            ]
        }

        stopped_by_button = False
        while True:
            stopped_by_button = (await get(f"stop_{task_id}")) == '1'
            if stopped_by_button:
                break
            async with aiohttp.ClientSession(timeout=None) as session:
                async with session.post("https://api.anthropic.com/v1/messages", headers=headers, json=data, timeout=None) as response:
                    if response.status == 200:
                        response_json = await response.json()
                        break
                    elif response.status == 429:
                        print('429 rate_limit_response')
                        await asyncio.sleep(1)
                    else:
                        stop = True
                        break

        if stopped_by_button:
            break

        if stop:
            await self.notify(
                "Api responded with not 200 status. Try again later",
                callbacks=['unlockRun']
            )

        if response_json['stop_reason'] == 'end_turn':
            with open(out_file, 'a') as f:
                f.write(response_json['content'][0]['text'])

            with open(out_file, 'r') as f:
                script_cleaner_last_answer_gpt = f.read()

            await update('script_cleaner_last_answer_gpt', script_cleaner_last_answer_gpt)

            await self.send_msg({
                'fn': 'update',
                'value': {
                    'state.script_cleaner_last_answer_gpt': script_cleaner_last_answer_gpt,
                    'progress': round(((idx + 1) / len(chunks)) * 100)
                }
            })
        else:
            await self.notify(
                "Model didn't reach a natural stopping point. To solve this problem try by lowering 'Size of chunk' parameter value",
                callbacks=['unlockRun']
            )
            stop = True
            break

        stop = (await get(f"stop_{task_id}")) == '1'
        if stop:
            break

    if not stop:
        await self.notify(f"Done. Result is in file {out_file}", callbacks=['unlockRun'])