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


    text_image_feedback_spiral_chat_gpt_max_tokens = models.IntegerField(
        verbose_name='Text-image feedback spiral max_tokens',
        default=1000
    )







    dall_e_prompt = models.TextField(
        max_length=100000,
        verbose_name='DALL-E prompt to generate image',
        default='Draw 3 circles'
    )
    dall_e_model = models.TextField(
        max_length=100,
        verbose_name='DALL-E model',
        default="dall-e-3"
    )
    dall_e_size = models.TextField(
        max_length=100,
        verbose_name='Image size',
        default="1024x1024"
    )
    dall_e_quality = models.TextField(
        choices=[('standard', 'Standard'), ('hd', 'hd')],
        default='standard',
        max_length=50,
        verbose_name='Image quality',
    )
    dall_e_n = models.IntegerField(
        verbose_name='n',
        default=1
    )


    suggest_changes_prompt = models.TextField(
        max_length=20000,
        verbose_name="'Suggest changes' prompt",
        default='What do you think it is better change in this image? Make your suggestions as prompt to dalle 3. Provide only suggestions as not numbered list and without any other text.'
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