from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, uid, email, name, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        if not uid:
            raise ValueError('UID is required')
        
        user = self.model(
            uid=uid,
            email=email,
            name=name,
            **extra_fields
        )
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, uid, email, name, password=None, **extra_fields):
        user = self.create_user(uid, email, name, password, **extra_fields)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class User(AbstractBaseUser):
    uid = models.CharField(max_length=128, unique=True)
    email = models.CharField(max_length=128, unique=True)
    profile_photo = models.URLField(blank=True, null=True)
    name = models.CharField(max_length=128)
    phone_number = models.CharField(max_length=128, null=True, blank=True)

    # Required fields for custom User model
    USERNAME_FIELD = 'uid'
    REQUIRED_FIELDS = ['email', 'name']
    
    objects = UserManager()  # Add this!
    
    def __str__(self):
        return self.email
