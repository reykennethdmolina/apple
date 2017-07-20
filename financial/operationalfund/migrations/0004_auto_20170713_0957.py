# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-07-13 09:57
from __future__ import unicode_literals

import datetime
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('operationalfund', '0003_auto_20170711_1630'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ofmain',
            name='atc',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='ofmain_atc_id', to='ataxcode.Ataxcode', validators=[django.core.validators.MinValueValidator(1)]),
        ),
        migrations.AlterField(
            model_name='ofmain',
            name='atcrate',
            field=models.IntegerField(blank=True, default=0, null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(100)]),
        ),
        migrations.AlterField(
            model_name='ofmain',
            name='deferredvat',
            field=models.CharField(blank=True, choices=[('Y', 'Yes'), ('N', 'No')], max_length=1, null=True),
        ),
        migrations.AlterField(
            model_name='ofmain',
            name='inputvattype',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='ofmain_inputvattype_id', to='inputvattype.Inputvattype'),
        ),
        migrations.AlterField(
            model_name='ofmain',
            name='modifydate',
            field=models.DateTimeField(default=datetime.datetime(2017, 7, 13, 9, 57, 54, 794000)),
        ),
        migrations.AlterField(
            model_name='ofmain',
            name='vat',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='ofmain_vat_id', to='vat.Vat', validators=[django.core.validators.MinValueValidator(1)]),
        ),
        migrations.AlterField(
            model_name='ofmain',
            name='vatrate',
            field=models.IntegerField(blank=True, default=0, null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(100)]),
        ),
    ]