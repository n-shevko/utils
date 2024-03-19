import os
import shlex

from app.utils import Common, get_config
from app.models import Config


def run2():
    config = get_config()
    folder_path, file_name = os.path.split(config.selected_video)

    base_name, _ = os.path.splitext(file_name)
    wav_exists = os.path.exists(os.path.join(folder_path, base_name + '.wav'))
    if not wav_exists or not config.use_existing_files:
        input_file = os.path.join('/videos', shlex.quote(file_name))
        out_file = os.path.join('/videos', shlex.quote(base_name + '.wav'))
        label = ttk.Label(frm, text="Extracting audio")
        label.grid(**layout['current_activity_message'])
        progressbar['value'] = 5
        active_containers.append('ffmpeg')
        response = docker(
            [(shlex.quote(folder_path), '/videos')],
            f"ffmpeg -i {input_file} -ar 16000 -ac 1 -c:a pcm_s16le -y {out_file}",
            'ffmpeg'
        )
        active_containers.remove('ffmpeg')
        label.grid_remove()
        if response != 0:
            notify("Audio extraction failed")
            return


class Worker(Common):
    def update_config(self, params):
        Config.objects.all().update(**params['config'])

    def script_cleaner_run(self, params):
        c = 3