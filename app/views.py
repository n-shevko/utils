import os

from django.shortcuts import render
from django.forms.models import model_to_dict
from django.http import JsonResponse

from app.utils import get_config


def main(request):
    context = {
        'data': {
            'config': model_to_dict(get_config()),
            'menu': [
                {'name': 'script_cleaner', 'label': 'Script cleaner'},
                # {'name': 'text_image_feedback_spiral', 'label': 'Text-image feedback spiral'},
                {'name': 'settings', 'label': 'Settings'}
            ]
        }
    }
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
