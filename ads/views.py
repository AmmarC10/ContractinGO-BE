from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Ad, AdType, Photo
from .serializers import AdSerializer, AdTypeSerializer
import uuid
import json
from contractingo.supabase_client import supabase

class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user

class AdViewSet(viewsets.ModelViewSet):
    # Want to work with all ads in the database
    queryset = Ad.objects.all()
    # Want to use the AdSerializer to serialize the data
    serializer_class = AdSerializer
    # Want to make sure the user is authenticated and only the owner can edit or delete the ad
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_destroy(self, instance):
        # Get all photo URLs before deletion
        photo_urls = list(instance.photos.values_list('image_url', flat=True))
        
        # Delete the ad (cascades to photos)
        instance.delete()
        
        # Delete from Supabase after database deletion
        for photo_url in photo_urls:
            if photo_url:
                filename = photo_url.split('/')[-1].split('?')[0]
                full_path = f"ad-photos/{filename}"
                supabase.storage.from_('ad-photos').remove([full_path])
    
    @action(detail=False, methods=['get'])
    def my_ads(self, request):
        ads = Ad.objects.filter(user=request.user)
        serializer = self.get_serializer(ads, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })   
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def getAllAdTypes(self, request):
        ad_types = AdType.objects.all()
        serializer = AdTypeSerializer(ad_types, many=True)
        return Response({
            'data': serializer.data
        })

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser], permission_classes=[permissions.AllowAny])
    def create_ad(self, request):
        ad_data_json = request.data.get('ad_data', {})
        ad_data = json.loads(ad_data_json)

        photos = request.FILES.getlist('photos')
       
        ad_data.pop('photo_1', None)
        ad_data.pop('photo_2', None)
        ad_data.pop('photo_3', None)

        ad_data['user'] = request.user.id

        serializer = self.get_serializer(data=ad_data)

        if serializer.is_valid():
            ad = serializer.save(user=request.user)

            for i, photo in enumerate(photos[:3]):
                photo_url = self.upload_to_supabase(photo, request.user.uid)
                Photo.objects.create(ad=ad, image_url=photo_url, order=i)

            response_serializer = self.get_serializer(ad)
            return Response({
                'success': True,
                'data': response_serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        ad_data_json = request.data.get('ad_data', {})
        request_data = json.loads(ad_data_json)
        
        # safety pops
        request_data.pop('photo_1', None)
        request_data.pop('photo_2', None)
        request_data.pop('photo_3', None)

        # Remove photos
        removed_photo_ids = request_data.pop('removed_photo_ids', [])

        if removed_photo_ids:
            photos_to_delete = instance.photos.filter(id__in=removed_photo_ids)

            for photo in photos_to_delete:
                filename = photo.image_url.split('/')[-1].split('?')[0]
                full_path = f"ad-photos/{filename}"
                supabase.storage.from_('ad-photos').remove([full_path])
            
            photos_to_delete.delete()
        
        photos = request.FILES.getlist('photos')
        for i, photo in enumerate(photos):
            photo_url = self.upload_to_supabase(photo, request.user.uid)
            Photo.objects.create(ad=instance, image_url=photo_url, order=instance.photos.count() + i)
                
        serializer = self.get_serializer(instance, data=request_data, partial=kwargs.get('partial', False))

        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_200_OK)
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

    

          
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_ads_by_type(request, ad_type_id):
    ads = Ad.objects.filter(ad_type_id=ad_type_id, is_active=True)
    serializer = AdSerializer(ads, many=True)
    return Response({
        'success': True,
        'data': serializer.data
    })

    


