# Generated by Django 2.1.1 on 2018-09-13 02:06

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lw2', '0012_auto_20180911_0232'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='posted_at',
            field=models.DateTimeField(default=datetime.datetime.today),
        ),
    ]
