# Generated by Django 5.1.5 on 2025-02-02 17:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot_app', '0002_alter_user_telegram_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='access_token',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='expiration_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
