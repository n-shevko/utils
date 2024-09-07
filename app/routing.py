from django.urls import re_path

from app.word_clouds import Worker


websocket_urlpatterns = [
    re_path(r"ws/worker$", Worker.as_asgi()),
]