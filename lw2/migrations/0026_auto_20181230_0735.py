# Generated by Django 2.1.2 on 2018-12-30 07:35

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('lw2', '0025_auth_groups_20181219_0834'),
    ]

    operations = [
        migrations.CreateModel(
            name='Invite',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=25)),
                ('date_created', models.DateTimeField(default=datetime.datetime.today)),
                ('used_date', models.DateTimeField(default=None, null=True)),
                ('expires', models.DateTimeField()),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='invites', to=settings.AUTH_USER_MODEL)),
                ('used_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='signup', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='InviteTreeNode',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('child', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='inv_children', to=settings.AUTH_USER_MODEL)),
                ('parent', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='inv_parent', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='comment',
            name='retracted',
            field=models.BooleanField(default=False),
        ),
    ]
