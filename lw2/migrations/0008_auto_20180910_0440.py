# Generated by Django 2.1.1 on 2018-09-10 04:40

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lw2', '0007_post_vote_count'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='posted_at',
            field=models.DateTimeField(default=datetime.datetime.today),
        ),
    ]
