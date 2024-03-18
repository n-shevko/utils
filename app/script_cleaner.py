from app.utils import Common, get_config
from app.models import Config


class Worker(Common):
    def update_config(self, params):
        Config.objects.all().update(**params['config'])

    def script_cleaner_run(self, params):
        c = 3