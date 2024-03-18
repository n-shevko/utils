from django.urls import path
from app.views import main, files


urlpatterns = [
    path("", main),
    path("files", files)
]