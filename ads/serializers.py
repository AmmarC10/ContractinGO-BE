from rest_framework import serializers
from .models import Ad, AdType, Photo, AdRequest, Review, City

class AdTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdType
        fields = ['id', 'name', 'icon']

class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ['id', 'name', 'province']

class PhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo
        fields = ['id', 'image_url', 'uploaded_at', 'order']

class AdSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    photos = PhotoSerializer(many=True, read_only=True)
    requests_count = serializers.SerializerMethodField()
    user_average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Ad
        fields = [
            'id', 'title', 'description', 'is_available_now', 
            'ad_type', 'user', 'user_name', 'photos',
            'location', 'tags', 'skills', 'created_at', 'updated_at', 'is_active', 
            'cost', 'requests_count', 'user_average_rating']
        
        read_only_fields =  ['user', 'user_name', 'created_at', 'requests_count', 'user_average_rating']
    
    def get_requests_count(self, obj):
        return obj.requests.filter(status='pending').count()

    def get_user_average_rating(self, obj):
        """Get the average rating of the ad owner"""
        reviews = Review.objects.filter(reviewee=obj.user)
        if not reviews.exists():
            return None
        
        from django.db.models import Avg
        average = reviews.aggregate(Avg('rating'))['rating__avg']
        return round(average, 1) if average else None

class AdRequestSerializer(serializers.ModelSerializer):
    requester_name = serializers.CharField(source='requester.name', read_only=True)
    ad_title = serializers.CharField(source='ad.title', read_only=True)
    ad_owner_name = serializers.CharField(source='ad.user.name', read_only=True)
    has_review = serializers.SerializerMethodField()
    
    class Meta:
        model = AdRequest
        fields = [
            'id', 'ad', 'ad_title', 'requester', 'requester_name', 
            'ad_owner_name', 'message', 'status', 'created_at', 
            'updated_at', 'owner_confirmed_completion', 
            'requester_confirmed_completion', 'has_review'
        ]
        read_only_fields = ['requester', 'requester_name', 'ad_title', 
                           'ad_owner_name', 'created_at', 'updated_at', 'has_review']
    
    def get_has_review(self, obj):
        return hasattr(obj, 'review')

class ReviewSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.CharField(source='reviewer.name', read_only=True)
    reviewee_name = serializers.CharField(source='reviewee.name', read_only=True)
    ad_title = serializers.CharField(source='ad_request.ad.title', read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id', 'ad_request', 'reviewer', 'reviewee', 'reviewer_name', 
            'reviewee_name', 'ad_title', 'rating', 'comment', 'created_at'
            ]
        read_only_fields = ['reviewer', 'reviewee', 'created_at', 
        'reviewer_name', 'reviewee_name', 'ad_title']
    
    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value
