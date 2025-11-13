from django.db import models
from supabase_auth.models import User

class AdType(models.Model):
    name = models.CharField(max_length=200)
    icon = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name

class City(models.Model):
    name = models.CharField(max_length=100)
    province = models.CharField(max_length=2, help_text="Two-letter province/territory code (e.g., ON, BC, QC)")
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Cities'
        unique_together = ['name', 'province']
    
    def __str__(self):
        return f"{self.name}, {self.province}"

class Ad(models.Model):

    # Ad fields
    title = models.CharField(max_length = 200)
    description = models.TextField()
    is_available_now = models.BooleanField(default=False)
    ad_type = models.ForeignKey(AdType, on_delete=models.PROTECT, related_name='adType')
    is_active = models.BooleanField(default=True)
    cost = models.CharField(max_length=200)

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

class Photo(models.Model):
    ad = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name='photos')
    image_url = models.URLField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'uploaded_at']

class AdRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    ad = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name='requests')
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ad_requests')
    message = models.TextField(blank=True, help_text="Optional message from requester")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Completion tracking
    owner_confirmed_completion = models.BooleanField(default=False)
    requester_confirmed_completion = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['ad', 'requester']  # One request per user per ad
    
    def __str__(self):
        return f"Request for {self.ad.title} by {self.requester.name}"

class Review(models.Model):
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]
    
    ad_request = models.OneToOneField(AdRequest, on_delete=models.CASCADE, related_name='review')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_given')
    reviewee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_received')
    rating = models.PositiveIntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.rating}-star review for {self.reviewee.name} by {self.reviewer.name}"



    
