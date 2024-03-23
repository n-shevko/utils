from django.db import models
from django.core.files.storage import FileSystemStorage
from django.conf import settings


class KeyValue(models.Model):
    key_field = models.CharField(max_length=250, default='', primary_key=True)
    value = models.TextField(max_length=100000, default='')

    class Meta:
        indexes = [models.Index(fields=['key_field'])]


class Config(models.Model):
    chatgpt_api_key = models.TextField(
        max_length=100,
        verbose_name='Chatgpt api key',
        default=""
    )
    chat_gpt_temperature = models.IntegerField(
        verbose_name='temperature',
        default=0
    )
    chat_gpt_top_p = models.IntegerField(
        verbose_name='top_p',
        default=1
    )
    chat_gpt_frequency_penalty = models.IntegerField(
        verbose_name='frequency_penalty',
        default=0
    )
    chat_gpt_presence_penalty = models.IntegerField(
        verbose_name='presence_penalty',
        default=0
    )

    class Meta:
        verbose_name = 'Settings'
        verbose_name_plural = 'Settings'

    def __str__(self):
        return 'Settings'


class Step(models.Model):
    dalle_request = models.TextField(
        max_length=100000,
        verbose_name='DALL-E prompt to generate image'
    )
    dalle_response = models.ImageField(
        storage=FileSystemStorage(location=settings.FILES_FOLDER)
    )
    suggest_changes_request = models.TextField(
        max_length=20000,
        verbose_name="'Suggest changes' request",
    )
    suggest_changes_response = models.TextField(
        max_length=10000,
        verbose_name="'Suggest changes' response",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Step'
        verbose_name_plural = 'Steps'
