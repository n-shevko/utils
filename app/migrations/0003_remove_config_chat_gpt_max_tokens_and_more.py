# Generated by Django 5.0.3 on 2024-03-18 18:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_config_current_tab'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='config',
            name='chat_gpt_max_tokens',
        ),
        migrations.AddField(
            model_name='config',
            name='percent_of_max_tokens_to_use_for_response',
            field=models.IntegerField(default=50, verbose_name='Percent of LLM context to use for response'),
        ),
        migrations.AddField(
            model_name='config',
            name='script_cleaner_prompt',
            field=models.CharField(default='You will be provided with statements, and your task is to convert them to standard English.', max_length=100000, verbose_name='Script cleaner prompt'),
        ),
        migrations.AddField(
            model_name='config',
            name='text_image_feedback_spiral_chat_gpt_max_tokens',
            field=models.IntegerField(default=1000, verbose_name='Text-image feedback spiral max_tokens'),
        ),
        migrations.AddField(
            model_name='config',
            name='use_existing_files',
            field=models.BooleanField(default=True, verbose_name='Use existing files'),
        ),
    ]
