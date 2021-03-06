# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-10-27 16:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Crawl',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.IntegerField(default=1000)),
                ('reg_date', models.DateTimeField(auto_now_add=True)),
                ('sns_kind', models.CharField(choices=[('in', 'instagram'), ('in', 'facebook')], default='in', max_length=2)),
                ('crawl_type', models.CharField(choices=[('all', 'all'), ('tags', 'tags')], default='all', max_length=5)),
                ('env', models.CharField(choices=[('pro', 'pro'), ('dev', 'dev'), ('test', 'test')], default='pro', max_length=5)),
                ('random', models.BooleanField(default=False)),
                ('query', models.CharField(blank=True, max_length=100, null=True)),
            ],
            options={
                'ordering': ('reg_date',),
            },
        ),
    ]
