# Generated by Django 5.0.3 on 2024-04-05 14:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_remove_config_dall_e_model_remove_config_dall_e_n_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='config',
            name='chatgpt_api_key',
            field=models.CharField(default='', max_length=100, verbose_name='OpenAI api key'),
        ),
    ]
