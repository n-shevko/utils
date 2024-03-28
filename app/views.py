import asyncio
import os

from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings

from app.models import KeyValue
from app.utils import get_config_sync, get, Async
from app.defaults import defaults
from app.text_image_feedback_spiral import get_images_from_folder


def main(request):
    current_tab = KeyValue.objects.filter(key_field='current_tab').first()
    current_tab = current_tab.value if current_tab else 'citations_recovering'
    get_config_sync()

    fields = defaults.get(current_tab, {}).keys()
    with Async() as loop:
        state = loop.run_until_complete(get(fields, force_dict=True))

    images = asyncio.run(get_images_from_folder())

    context = {
        'data': {
            'current_tab': current_tab,
            'state': state,
            'menu': [
                {'name': 'citations_recovering', 'label': 'Citations recovering'},
                {'name': 'script_cleaner', 'label': 'Script cleaner'},
                {'name': 'text_image_feedback_spiral', 'label': 'Text-image feedback spiral'},
                #  {'name': 'settings', 'label': 'Settings'}
            ],
            'images': images
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
