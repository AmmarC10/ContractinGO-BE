from django.db import models

class User(models.Model):
    uid = models.CharField(max_length=128, unique=True)
    email = models.CharField(max_length=128, unique=True)
    profile_photo = models.URLField(blank=True, null=True)
    name = models.CharField(max_length=128)
    phone_number = models.CharField(max_length=128, null=True)
