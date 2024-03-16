from app.utils import Common, get_config


class Worker(Common):
    def switch_tab(self, params):
        config = get_config()
        config.current_tab = params['name']
        config.save()