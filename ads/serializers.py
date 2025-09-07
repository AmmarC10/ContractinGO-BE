from rest_framework import serializers
from .models import Ad, AdType, Photo

class AdTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdType
        fields = ['id', 'name', 'icon']

class PhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo
        fields = ['id', 'image_url', 'uploaded_at', 'order']

class AdSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    photos = PhotoSerializer(many=True, read_only=True)

    class Meta:
        model = Ad
        fields = [
            'id', 'title', 'description', 'is_available_now', 
            'ad_type', 'user', 'user_name', 'photos',
            'location', 'tags', 'skills', 'created_at', 'updated_at', 'is_active', 
            'cost']
        
        read_only_fields =  ['user', 'user_name', 'created_at']
