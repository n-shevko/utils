from django.shortcuts import render
from django.forms.models import model_to_dict

from app.utils import get_config


# https://github.com/cubiclesoft/js-fileexplorer

def main(request):
    context = {
        'data': {
            'config': model_to_dict(get_config()),
            'menu': [
                {'name': 'script_cleaner', 'label': 'Script cleaner'},
                {'name': 'text_image_feedback_spiral', 'label': 'Text-image feedback spiral'},
                {'name': 'settings', 'label': 'Settings'}
            ]
        }
    }
    return render(request, "main.html", context)
