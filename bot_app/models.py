from django.db import models

# Create your models here.
class User(models.Model):
    telegram_id = models.BigIntegerField(primary_key=True)
    username = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    access_token = models.CharField(max_length=255, blank=True, null=True)  # Adjust length as necessary
    expiration_date = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.username} ({self.telegram_id})"