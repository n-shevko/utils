# Generated by Django 5.0.3 on 2024-04-05 16:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_alter_config_chatgpt_api_key'),
    ]

    operations = [
        migrations.AlterField(
            model_name='config',
            name='chat_gpt_frequency_penalty',
            field=models.FloatField(default=0, help_text='This parameter is used to discourage the model from repeating the same words or phrases too frequently\n         within the generated text. It is a value that is added to the log-probability of a token each time it occurs \n         in the generated text. A higher frequency_penalty value will result in the model being more conservative in \n         its use of repeated tokens.', verbose_name='frequency_penalty'),
        ),
        migrations.AlterField(
            model_name='config',
            name='chat_gpt_presence_penalty',
            field=models.FloatField(default=0, help_text='\n        This parameter is used to encourage the model to include a diverse range of tokens in the generated text. \n        It is a value that is subtracted from the log-probability of a token each time it is generated.\n        A higher presence_penalty value will result in the model being more likely to generate tokens\n        that have not yet been included in the generated text.\n        ', verbose_name='presence_penalty'),
        ),
        migrations.AlterField(
            model_name='config',
            name='chat_gpt_temperature',
            field=models.FloatField(default=0, help_text='Controls the “creativity” or randomness of the text generated by GPT. A higher temperature (e.g., 0.7)\n        results in more diverse and creative output, while a lower temperature (e.g., 0.2) \n        makes the output more deterministic and focused.\n        <br><br>\n        In practice, temperature affects the probability distribution over the possible tokens \n        at each step of the generation process. A temperature of 0 would make the model completely deterministic, \n        always choosing the most likely token.\n        ', verbose_name='temperature'),
        ),
        migrations.AlterField(
            model_name='config',
            name='chat_gpt_top_p',
            field=models.FloatField(default=1, help_text='Top_p sampling is an alternative to temperature sampling. Instead of considering all possible tokens,\n         GPT considers only a subset of tokens (the nucleus) whose cumulative probability mass adds up to a certain threshold (top_p).\n         <br><br>\n         For example, if top_p is set to 0.1, GPT will consider only the tokens that make up the top 10% of the probability \n         mass for the next token. This allows for dynamic vocabulary selection based on context.\n         ', verbose_name='top_p'),
        ),
    ]
