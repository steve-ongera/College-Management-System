# Generated by Django 5.2 on 2025-07-08 09:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coreapplication', '0008_newsarticle'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='gender',
            field=models.CharField(blank=True, choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')], max_length=10),
        ),
    ]
