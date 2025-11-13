from django.db import models
from ads.models import Ad
from supabase_auth.models import User

class Conversation(models.Model):
    ad = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name='conversations')
    participants = models.ManyToManyField(User, related_name='user_conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Conversation about {self.ad.title}"

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender.name}: {self.content[:50]}..."

class MessageAttachment(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments')
    image_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Attachment for message {self.message.id}"