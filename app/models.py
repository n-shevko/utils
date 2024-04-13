from django.db import models
from django.core.files.storage import FileSystemStorage
from django.conf import settings


class KeyValue(models.Model):
    key_field = models.CharField(max_length=250, default='', primary_key=True)
    value = models.TextField(max_length=100000, default='')

    class Meta:
        indexes = [models.Index(fields=['key_field'])]


class Config(models.Model):
    chatgpt_api_key = models.CharField(
        max_length=100,
        verbose_name='OpenAI api key',
        default="",
        blank=True,
        help_text='''Can be found <a target='_blank' href='https://platform.openai.com/api-keys'>here</a>'''
    )
    chat_gpt_temperature = models.FloatField(
        verbose_name='temperature',
        default=1.0,
        help_text='''
        What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random,
        while lower values like 0.2 will make it more focused and deterministic.
<br>
We generally recommend altering this or top_p but not both.
        '''
    )
    chat_gpt_top_p = models.FloatField(
        verbose_name='top_p',
        default=1,
        help_text='''An alternative to sampling with temperature, called nucleus sampling, where the model considers
         the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 
         10% probability mass are considered.
         <br>
         We generally recommend altering this or temperature but not both
         '''
    )
    chat_gpt_frequency_penalty = models.FloatField(
        verbose_name='frequency_penalty',
        default=0,
        help_text='''Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing 
        frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.
<br>
 <a target='_blank' href='https://platform.openai.com/docs/guides/text-generation/parameter-details'>
 more information about frequency and presence penalties.</a>
'''
    )
    chat_gpt_presence_penalty = models.FloatField(
        verbose_name='presence_penalty',
        default=0,
        help_text='''
Number between -2.0 and 2.0. Positive values penalize new tokens based on whether they appear in the text so far,
 increasing the model's likelihood to talk about new topics.
<br>
 <a target='_blank' href='https://platform.openai.com/docs/guides/text-generation/parameter-details'>
 more information about frequency and presence penalties.</a>
        '''
    )

    claude_api_key = models.CharField(
        max_length=200,
        verbose_name='Claude api key',
        default="",
        blank=True,
        help_text='''Can be found <a target='_blank' href='https://console.anthropic.com/settings/keys'>here</a>'''
    )
    claude_temperature = models.FloatField(
        verbose_name='temperature',
        default=1,
        help_text='''Amount of randomness injected into the response.
Ranges from 0.0 to 1.0. Use temperature closer to 0.0 for analytical / multiple choice, and closer to 1.0 for creative and generative tasks.

Note that even with temperature of 0.0, the results will not be fully deterministic.
        '''
    )

    dall_e_quality = models.CharField(
        max_length=100,
        verbose_name='Quality',
        choices=(
            ('standard', 'standard'),
            ('hd', 'hd')
        ),
        default='standard',
        help_text='''The quality of the image that will be generated.
         hd creates images with finer details and greater consistency across the image.'''
    )
    dall_e_size = models.CharField(
        max_length=100,
        verbose_name='Image size',
        choices=(
            ('1024x1024', '1024x1024'),
            ('1792x1024', '1792x1024'),
            ('1024x1792', '1024x1792')
        ),
        default='1024x1024'
    )
    dall_e_style = models.CharField(
        max_length=100,
        verbose_name='Style',
        choices=(
            ('vivid', 'vivid'),
            ('natural', 'natural')
        ),
        default='vivid',
        help_text='''The style of the generated images. Must be one of vivid or natural. 
        Vivid causes the model to lean towards generating hyper-real and dramatic images.
        Natural causes the model to produce more natural, less hyper-real looking images. '''
    )
    dall_e_show_last_images = models.IntegerField(
        verbose_name='Show last images',
        default=5
    )

    class Meta:
        verbose_name = 'Settings'
        verbose_name_plural = 'Settings'

    def __str__(self):
        return 'Settings'


class Step(models.Model):
    dalle_request = models.TextField(
        max_length=100000,
        verbose_name='DALL-E prompt to generate image',
    )
    revised_prompt = models.TextField(
        max_length=100000,
        verbose_name='Revised DALL-E prompt',
        help_text='The prompt that was used to generate the image, if there was any revision to the prompt.'
    )
    dalle_response = models.ImageField(
        storage=FileSystemStorage(location=settings.MEDIA_ROOT)
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
