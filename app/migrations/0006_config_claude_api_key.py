# Generated by Django 5.0.3 on 2024-04-05 22:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0005_alter_config_chatgpt_api_key'),
    ]

    operations = [
        migrations.AddField(
            model_name='config',
            name='claude_api_key',
            field=models.CharField(blank=True, default='', help_text="Can be found <a target='_blank' href='https://console.anthropic.com/settings/keys'>here</a>", max_length=200, verbose_name='Claude api key'),
        ),
    ]
