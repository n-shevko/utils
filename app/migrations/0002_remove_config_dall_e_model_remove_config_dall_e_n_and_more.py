# Generated by Django 5.0.3 on 2024-03-23 19:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='config',
            name='dall_e_model',
        ),
        migrations.RemoveField(
            model_name='config',
            name='dall_e_n',
        ),
        migrations.RemoveField(
            model_name='config',
            name='dall_e_prompt',
        ),
        migrations.RemoveField(
            model_name='config',
            name='dall_e_quality',
        ),
        migrations.RemoveField(
            model_name='config',
            name='dall_e_size',
        ),
        migrations.RemoveField(
            model_name='config',
            name='suggest_changes_prompt',
        ),
        migrations.RemoveField(
            model_name='config',
            name='text_image_feedback_spiral_chat_gpt_max_tokens',
        ),
    ]