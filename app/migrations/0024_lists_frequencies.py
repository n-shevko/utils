# Generated by Django 5.0.3 on 2024-09-06 16:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0023_lists'),
    ]

    operations = [
        migrations.AddField(
            model_name='lists',
            name='frequencies',
            field=models.CharField(default='', max_length=100),
        ),
    ]
