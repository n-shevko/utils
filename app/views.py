from django.shortcuts import render

from app.utils import get_config


def main(request):
    context = {
        'config': get_config(),
        'menu': [
            {'name': 'text_image_feedback_spiral', 'label': 'Text-image feedback spiral'},
            {'name': 'settings', 'label': 'Settings'}
        ]
    }
    return render(request, "main.html", context)
