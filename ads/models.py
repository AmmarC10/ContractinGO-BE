from django.db import models
from firebase_auth.models import User

class AdType(models.Model):
    name = models.CharField(max_length=200)
    icon = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name

class Ad(models.Model):

    # Ad fields
    title = models.CharField(max_length = 200)
    description = models.TextField()
    is_available_now = models.BooleanField(default=False)
    ad_type = models.ForeignKey(AdType, on_delete=models.PROTECT, related_name='adType')
    is_active = models.BooleanField(default=True)
    cost = models.CharField(max_length=200)

    # Photos
    photo_1 = models.URLField(blank=True, null=True)
    photo_2 = models.URLField(blank=True, null=True)
    photo_3 = models.URLField(blank=True, null=True)

    # Search optimization fields
    location = models.CharField(max_length=200, blank=True, help_text="City / General Area")
    tags = models.CharField(max_length = 200, blank=True, help_text="Comma-separated tags like: wedding (for photography), blog (for website)")
    skills = models.CharField(max_length = 200, blank=True, help_text="Comma-separated skills like: Photoshop, Django, etc.")

    # User relationship
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ads')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['tags']),
            models.Index(fields=['location']),
            models.Index(fields=['ad_type']),
            models.Index(fields=['is_available_now'])
        ]
    
    def __str__(self):
        return f"{self.title} by {self.user.name}"

    
