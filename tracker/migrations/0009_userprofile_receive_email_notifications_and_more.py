# Generated by Django 5.2 on 2025-05-06 14:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0008_usersettings'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='receive_email_notifications',
            field=models.BooleanField(default=True),
        ),
        migrations.DeleteModel(
            name='UserSettings',
        ),
    ]
