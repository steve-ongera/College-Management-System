# Generated by Django 5.2 on 2025-07-05 12:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coreapplication', '0003_student_current_year'),
    ]

    operations = [
        migrations.AddField(
            model_name='subject',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
