import json
import aiomysql
import asyncio

from channels.generic.websocket import AsyncWebsocketConsumer
from app.models import Config
from app.defaults import defaults


class db():
    async def __aenter__(self):
        self.conn = await aiomysql.connect(
            host='127.0.0.1',
            port=3306,
            user='nikos',
            password='123',
            db='data'
        )
        self.cur = await self.conn.cursor(aiomysql.DictCursor)
        return self.cur

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cur.close()
        await self.conn.commit()
        self.conn.close()


class Async:
    def __enter__(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        return self.loop

    def __exit__(self, exc_type, exc_value, traceback):
        self.loop.close()


def get_config_sync() -> Config:
    config = Config.objects.first()
    if not config:
        Config().save()
        config = Config.objects.first()
    return config


async def get_config():
    async with db() as c:
        await c.execute('select * from app_config')
        ls = await c.fetchall()
        return ls[0]


defaults2 = {}
for _, item in defaults.items():
    defaults2.update(item)


async def get(key, default=None):
    if not key:
        return {}
    async with db() as c:
        if isinstance(key, str):
            key = [key]
        keys = tuple(key)
        placeholders = ', '.join(['%s'] * len(keys))
        await c.execute(f'select * from app_keyvalue where key_field in ({placeholders})', keys)
        ls = await c.fetchall()
        result = {}
        for item in ls:
            result[item['key_field']] = item['value']
        for k in (set(keys) - set(result.keys())):
            if k not in defaults2:
                continue

            result[k] = defaults2[k]
        if len(keys) == 1:
            if result:
                return list(result.values())[0]
            else:
                return default
        else:
            return result


async def update(key, value):
    async with db() as c:
        value = str(value)
        await c.execute(
            'INSERT INTO app_keyvalue (key_field, value) VALUES (%s, %s) ON DUPLICATE KEY UPDATE value = %s',
            (key, value, value)
        )


class Common(AsyncWebsocketConsumer):
    background_tasks = set()

    async def send_msg(self, msg):
        await self.send(text_data=json.dumps(msg))

    async def update(self, params):
        await update(params['key'], params['value'])

    async def get_state(self, params):
        keys = defaults.get(params['current_tab'], [])
        await self.send_msg({
            'fn': 'update',
            'value': {'state': await get(keys)}
        })

    async def notify(self, msg):
        await self.send_msg({
            'fn': 'update',
            'value': {
                'dialog': 'notify_dialog',
                'dialogTitle': 'Notification',
                'msg': msg
            },
            'callback': 'initModal'
        })

    async def receive(self, text_data):
        request = json.loads(text_data)
        # https://docs.python.org/3/library/asyncio-task.html#asyncio.create_task
        task = asyncio.create_task(getattr(self, request['fn'])(request))
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)