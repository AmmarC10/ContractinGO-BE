from rest_framework import serializers
from .models import Ad

class AdSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    photos = serializers.SerializerMethodField()

    class Meta:
        model = Ad
        fields = [
            'id', 'title', 'description', 'is_available_now', 
            'ad_type', 'user', 'user_name', 'photo_1', 'photo_2', 'photo_3',
            'location', 'tags', 'skills', 'created_at', 'updated_at', 'is_active']
        
        readOnlyFields =  ['user', 'user_name', 'created_at']