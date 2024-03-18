import json

from channels.generic.websocket import WebsocketConsumer
from app.models import Config


def get_config():
    config = Config.objects.first()
    if not config:
        config = Config().save()
    return config


class Common(WebsocketConsumer):
    def switch_tab(self, params):
        config = get_config()
        config.current_tab = params['name']
        config.save()

    def receive(self, text_data):
        request = json.loads(text_data)
        response = getattr(self, request['fn'])(request)
        if response is not None:
            self.send(text_data=json.dumps({
                'type': request['fn'],
                'response': response
            }))