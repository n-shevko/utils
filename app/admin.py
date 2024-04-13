from django.contrib import admin

from app.models import Config, Step


class ConfigAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Chat GPT', {
            'fields': (
                'chatgpt_api_key',
                'chat_gpt_temperature',
                'chat_gpt_top_p',
                'chat_gpt_frequency_penalty',
                'chat_gpt_presence_penalty'
            )
        }),
        ('Claude', {
            'fields': (
                'claude_api_key',
                'claude_temperature'
            ),
        }),
        ('Dall-e', {
            'fields': (
                'dall_e_quality',
                'dall_e_size',
                'dall_e_style',
                'dall_e_show_last_images'
            )
        })
    )


admin.site.register(Config, ConfigAdmin)
admin.site.register(Step)