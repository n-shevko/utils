from django.urls import re_path

from app.text_image_feedback_spiral import Worker


websocket_urlpatterns = [
    re_path(r"ws/worker$", Worker.as_asgi()),
]