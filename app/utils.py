import json
import aiomysql
import asyncio

from channels.generic.websocket import AsyncWebsocketConsumer
from app.models import Config


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


class Common(AsyncWebsocketConsumer):
    async def switch_tab(self, params):
        async with db() as c:
            await c.execute('update app_config set current_tab = %s', (params['name'],))

    async def send_msg(self, msg):
        await self.send(text_data=json.dumps(msg))

    async def receive(self, text_data):
        request = json.loads(text_data)
        asyncio.create_task(getattr(self, request['fn'])(request))