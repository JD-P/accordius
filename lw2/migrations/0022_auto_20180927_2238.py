# Generated by Django 2.1.1 on 2018-09-27 22:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lw2', '0021_auto_20180927_2019'),
    ]

    operations = [
        migrations.RenameField(
            model_name='message',
            old_name='content',
            new_name='body',
        ),
    ]