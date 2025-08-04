from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Ad
from .serializers import AdSerializer
import uuid
import json
from contractingo.supabase_client import supabase

class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user

class AdViewSet(viewsets.ModelViewSet):
    queryset = Ad.objects.all()
    serializer_class = AdSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_destroy(self, instance):
        instance.delete()
    
    @action(detail=False, methods=['get'])
    def my_ads(self, request):
        ads = Ad.objects.filter(user=request.user)
        serializer = self.get_serializer(ads, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })   

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def create_ad(self, request):
        if request.content_type.startswith('multipart/form-data'):
            ad_data_json = request.data.get('ad_data', {})
            ad_data = json.loads(ad_data_json)

            photos = request.FILES.getlist('photos')
            photo_urls = []

            for i, photo in enumerate(photos[:3]):
                photo_url = self.upload_to_supabase(photo, request.user.uid)
                photo_urls.append(photo_url)
            
            for i, photo_url in enumerate(photo_urls, 1):
                ad_data[f'photo_{i}'] = photo_url
        else:
            ad_data = request.data
            photos = []

        ad_data['user'] = request.user.id

        serializer = self.get_serializer(data=ad_data)

        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


    def upload_to_supabase(self, file_obj, user_uid):
        filename = f"{user_uid}_{uuid.uuid4()}.jpg"
        filePath = f"ad-photos/{filename}"

        result = supabase.storage.from_('ad-photos').upload(
            path=filePath, 
            file=file_obj.read(),
            file_options={'content-type': file_obj.content_type})

        photo_url = supabase.storage.from_('ad-photos').get_public_url(filePath)
        return photo_url  


