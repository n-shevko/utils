from django.urls import path
from app.views import *


urlpatterns = [
    path("", main),
    path("files", files),
    path("save_png", save_png)
]