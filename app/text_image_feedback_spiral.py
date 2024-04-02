import os
import aiohttp
import asyncio
import aiofiles
from pathlib import Path
from datetime import datetime
from openai import AsyncOpenAI


async def create_openai_client(api_key):
    client = AsyncOpenAI(api_key=api_key)
    return client


async def generate_image_url(client):
    response = await client.images.generate(model="dall-e-3", prompt="draw 3 circles", size="1024x1024",
                                            quality="standard", n=1)
    image_url = response.data[0].url
    print(image_url)
    return image_url


async def download_and_save_image(image_url, is_docker_prod=None):
    try:
        if is_docker_prod:
            # Если запущено в Docker в режиме prod, сохраняем изображения в папку service_data
            service_data_path = os.getenv('USER_DATA')
            if service_data_path is None:
                print("Переменная окружения USER_DATA не установлена")
                return

            out_folder = service_data_path
        else:
            # Если не запущено в Docker в режиме prod, сохраняем изображения в локальную папку service_data
            current_directory = await asyncio.to_thread(str, Path.cwd())
            out_folder = await asyncio.to_thread(os.path.join, current_directory, str('service_data'))

        await asyncio.to_thread(os.makedirs, out_folder, exist_ok=True, mode=0o777)

        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                if response.status == 200:
                    extension = image_url.split('?')[0].split('.')[-1]
                    print(extension)
                    now = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
                    filename = f"dalle_response_{now}.{extension}"
                    async with aiofiles.open(os.path.join(out_folder, filename), "wb") as file:
                        while True:
                            chunk = await response.content.read(1024)
                            if not chunk:
                                break
                            await file.write(chunk)
    except Exception as e:
        print(f"An error occurred while saving image: {e}")


async def get_images_from_folder(is_docker_prod=None):
    try:
        if is_docker_prod:
            service_data_path = os.getenv('USER_DATA')
            if service_data_path is None:
                print("Переменная окружения USER_DATA не установлена")
                return []

            service_data_folder = os.path.join(service_data_path, 'service_data')
        else:
            current_directory = await asyncio.to_thread(Path.cwd)
            app_folder = await asyncio.to_thread(current_directory.joinpath, "app")
            service_data_folder = await asyncio.to_thread(app_folder.joinpath, "service_data")

        files = await asyncio.to_thread(os.listdir, service_data_folder)

        images = await asyncio.gather(*[
            asyncio.to_thread(os.path.join, service_data_folder, file)
            for file in files
            if await asyncio.to_thread(os.path.isfile, os.path.join(service_data_folder, file))
        ])

        return images
    except Exception as e:
        print(f"An error occurred while getting images from folder: {e}")
        return []


async def ask_chatgpt_for_feedback(client, image_url, prompt):
    chatgpt_settings = {
        "model": "gpt-4-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": image_url},
                    },
                    {
                        "type": "text",
                        "text": prompt,
                    }
                ]
            }
        ]
    }
    response = await client.chat.completions.create(**chatgpt_settings)
    feedback = response.choices[0].message.content
    print(feedback)
    return feedback
