# Generated by Django 5.2 on 2025-07-04 14:44

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coreapplication', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='subject',
            name='year',
            field=models.IntegerField(default=1, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)]),
        ),
    ]
