# Generated by Django 5.0.3 on 2024-09-05 19:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0021_remove_wordfreqs_year_wordfreqs_source_file'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='wordfreqs',
            name='source_file',
        ),
        migrations.AddField(
            model_name='wordfreqs',
            name='year',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
