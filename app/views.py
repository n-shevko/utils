import json
import os

from django.shortcuts import render
from django.http import JsonResponse

from app.models import KeyValue
from app.utils import get_config_sync, get, Async
from app.defaults import defaults
from binascii import a2b_base64

from django.views.decorators.csrf import csrf_exempt
import shlex
from datetime import datetime
from django.conf import settings

from django.contrib.admin.views.decorators import staff_member_required


# @staff_member_required
def main(request):
    current_tab = KeyValue.objects.filter(key_field='current_tab').first()
    current_tab = current_tab.value if current_tab else 'citations_recovering'
    get_config_sync()

    fields = defaults.get(current_tab, {}).keys()
    with Async() as loop:
        state = loop.run_until_complete(get(fields, force_dict=True))
    context = {
        'data': {
            'current_tab': current_tab,
            'state': state,
            'menu': [
                {'name': 'margin_revisions_acceptor', 'label': 'Margin revisions acceptor'},
                {'name': 'citations_recovering', 'label': 'Citations recovering'},
                {'name': 'script_cleaner', 'label': 'Script cleaner'},
                {'name': 'text_image_feedback_spiral', 'label': 'Text-image feedback spiral'},
                {'name': 'word_clouds', 'label': 'Word clouds'},
                {'name': 'settings', 'label': 'Settings'}
            ]
        }
    }

    with open(os.path.join(settings.BASE_DIR, 'app', 'templates', f"template.html"), 'r') as file:
        template2 = file.read()

    for item in context['data']['menu']:
        template = os.path.join(settings.BASE_DIR, 'app', 'templates', f"{item['name']}.html")
        if not os.path.exists(template):
            with open(template, 'w') as file:
                file.write(template2.replace('{{current_tab}}', item['name']))

        js = os.path.join(settings.BASE_DIR, 'app', 'static', 'js', f"{item['name']}.js")
        if not os.path.exists(js):
            with open(js, 'w') as file:
                file.write(f"{item['name']} = {{}}")

    return render(request, "main.html", context)


def files(request):
    id = request.GET['id']
    if id == '#':
        if 'USER_DATA' in os.environ:
            path = os.environ['USER_DATA']
        else:
            path = os.path.expanduser('~')
    else:
        path = id
    folders = []
    files = []
    for item in sorted(os.listdir(path)):
        full_path = os.path.join(path, item)
        if os.path.isdir(full_path):
            folders.append(
                {"id": full_path, "parent": id, "text": item, "children": True}
            )
        else:
            files.append(
                {"id": full_path, "parent": id, "text": item, 'icon': 'jstree-file'}
            )
    return JsonResponse(folders + files, safe=False)


@csrf_exempt
def save_png(request):
    body = json.loads(request.body.decode('utf-8'))
    images = []
    for item in body:
        path = os.path.join('/tmp', f"{item['year']}.png")
        with open(path, "wb") as fh:
            data = item['image'].replace("data:image/png;base64,", "")
            binary_data = a2b_base64(data)
            fh.write(binary_data)
        images.append({'path': path, 'year': item['year']})



    config = {}
    for item in KeyValue.objects.filter(key_field__in=['screen_width', 'screen_height', 'folder_with_pdfs', 'year_duration']):
        config[item.key_field] = item.value

    with open('/tmp/for_manim.txt', 'w') as file:
        file.write(json.dumps(
            {
                'images': images,
                'year_duration': config['year_duration']
            }
        ))


    formatted_datetime = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    out = shlex.quote(os.path.join(config['folder_with_pdfs'], f"{formatted_datetime}.mp4"))
    script = os.path.join(settings.BASE_DIR, 'app', 'word_clouds_manim.py')
    cmd = f"manim {script} -r {config['screen_width']},{config['screen_height']} --disable_caching --media_dir /service_data/media ImageSlideshow -o {out}"
    res = os.system(cmd)
    if res == 0:
        return JsonResponse({'out': out}, safe=False)
    else:
        return JsonResponse({'error': cmd}, safe=False)