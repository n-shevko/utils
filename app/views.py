import os
import asyncio

from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings

from app.models import KeyValue
from app.utils import get_config_sync, get, Async
from app.defaults import defaults


def main(request):
    current_tab = KeyValue.objects.filter(key_field='current_tab').first()
    current_tab = current_tab.value if current_tab else 'script_cleaner'
    get_config_sync()

    fields = defaults.get(current_tab, {}).keys()
    with Async() as loop:
        state = loop.run_until_complete(get(fields, force_dict=True))
    context = {
        'data': {
            'current_tab': current_tab,
            'state': state,
            'menu': [
                {'name': 'citations_recovering', 'label': 'Citations recovering'},
                {'name': 'script_cleaner', 'label': 'Script cleaner'},
                {'name': 'text_image_feedback_spiral', 'label': 'Text-image feedback spiral'},
                {'name': 'settings', 'label': 'Settings'}
            ]
        }
    }

    with open(os.path.join(settings.BASE_DIR, 'app', 'templates', f"template.html"), 'r') as file:
        template2 = file.read()

    for item in context['data']['menu']:
        template = os.path.join(settings.BASE_DIR, 'app', 'templates',  f"{item['name']}.html")
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
    response = []
    if id == '#':
        path = '/home/nikos'
    else:
        path = id
    for item in sorted(os.listdir(path), key=len):
        full_path = os.path.join(path, item)
        if os.path.isdir(full_path):
            response.append(
                {"id": full_path,  "parent": id, "text": item, "children": True}
            )
        else:
            response.append(
                {"id": full_path, "parent": id, "text": item, 'icon': 'jstree-file'}
            )
    return JsonResponse(response, safe=False)
