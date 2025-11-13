from rest_framework import serializers
from django.db import models
from .models import User


class UserSerializer(serializers.ModelSerializer):
    average_rating = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'uid', 'email', 'name', 'profile_photo', 'phone_number', 'average_rating']
        read_only_fields = ['id', 'uid', 'average_rating']
    
    def get_average_rating(self, obj):
        """
        Calculate the average rating for this user based on all reviews they received.
        Returns None if the user has no reviews.
        """
        from ads.models import Review 
        
        reviews = Review.objects.filter(reviewee=obj)
        if not reviews.exists():
            return None
        
        average = reviews.aggregate(models.Avg('rating'))['rating__avg']
        # Round to 1 decimal place
        return round(average, 1) if average else None
