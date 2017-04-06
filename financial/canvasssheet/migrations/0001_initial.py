# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-04-03 14:28
from __future__ import unicode_literals

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Csmain',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('csnum', models.CharField(max_length=10, unique=True)),
                ('csdate', models.DateField()),
                ('cstype', models.CharField(choices=[('MSRF', 'MSRF')], default='MSRF', max_length=10)),
                ('csstatus', models.CharField(choices=[('F', 'For Approval'), ('A', 'Approved'), ('D', 'Disapproved')], default='F', max_length=1)),
                ('particulars', models.TextField()),
                ('remarks', models.CharField(blank=True, max_length=250, null=True)),
                ('status', models.CharField(choices=[('A', 'Active'), ('I', 'Inactive'), ('C', 'Cancelled'), ('O', 'Posted'), ('P', 'Printed')], default='A', max_length=1)),
                ('enterdate', models.DateTimeField(auto_now_add=True)),
                ('modifydate', models.DateTimeField(default=datetime.datetime(2017, 4, 3, 14, 28, 34, 177000))),
                ('postdate', models.DateTimeField(blank=True, null=True)),
                ('isdeleted', models.IntegerField(default=0)),
                ('approverresponse', models.CharField(blank=True, choices=[('A', 'Approved'), ('D', 'Disapproved')], max_length=1, null=True)),
                ('responsedate', models.DateTimeField(blank=True, null=True)),
                ('actualapprover', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='csactual_approver', to=settings.AUTH_USER_MODEL)),
                ('designatedapprover', models.ForeignKey(default=2, on_delete=django.db.models.deletion.CASCADE, related_name='csdesignated_approver', to=settings.AUTH_USER_MODEL)),
                ('enterby', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='csmain_enter', to=settings.AUTH_USER_MODEL)),
                ('modifyby', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='csmain_modify', to=settings.AUTH_USER_MODEL)),
                ('postby', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='csmain_post', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-pk'],
                'db_table': 'csmain',
            },
        ),
    ]
