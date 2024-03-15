from django.urls import path
from app.views import main


urlpatterns = [
    path("", main)
]