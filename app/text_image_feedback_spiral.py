from utils import Common


class Worker(Common):
    def ping(self, params):
        return 'pong'