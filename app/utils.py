import json
import aiomysql
import asyncio

from channels.generic.websocket import AsyncWebsocketConsumer
from app.models import Config, KeyValue
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


async def get(key, default=None):
    async with db() as c:
        await c.execute('select * from app_keyvalue where key_field = %s', (key,))
        ls = await c.fetchall()
        if ls:
            return ls[0]['value']
        else:
            for _, item in defaults.items():
                res = item.get(key)
                if res is not None:
                    return res
            return default


async def update(key, value):
    async with db() as c:
        value = str(value)
        await c.execute(
            'INSERT INTO app_keyvalue (key_field, value) VALUES (%s, %s) ON DUPLICATE KEY UPDATE value = %s',
            (key, value, value)
        )


def get_with_defaults(key_to_default):
    result = dict([(obj.key_field, obj.value) for obj in KeyValue.objects.filter(key_field__in=key_to_default.keys())])
    tmp = set(key_to_default.keys()) - set(result.keys())
    for key in tmp:
        result[key] = key_to_default[key]
    return result


class Common(AsyncWebsocketConsumer):
    background_tasks = set()

    async def send_msg(self, msg):
        await self.send(text_data=json.dumps(msg))

    async def update(self, params):
        await update(params['key'], params['value'])

    async def receive(self, text_data):
        request = json.loads(text_data)
        # https://docs.python.org/3/library/asyncio-task.html#asyncio.create_task
        task = asyncio.create_task(getattr(self, request['fn'])(request))
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)
