# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2018-02-23 06:03
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('companyparameter', '0017_auto_20180222_1431'),
    ]

    operations = [
        migrations.AddField(
            model_name='companyparameter',
            name='pcv_final_approver',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='companyparameter_pcv_final_approver', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='companyparameter',
            name='pcv_initial_approver',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='companyparameter_pcv_initial_approver', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='companyparameter',
            name='rfv_final_approver',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='companyparameter_rfv_final_approver', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='companyparameter',
            name='rfv_initial_approver',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='companyparameter_rfv_initial_approver', to=settings.AUTH_USER_MODEL),
        ),
    ]