from django.urls import re_path

from app.script_cleaner import Worker


websocket_urlpatterns = [
    re_path(r"ws/worker$", Worker.as_asgi()),
]