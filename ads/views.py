from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Ad, AdType
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
        instance.delete()
    
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
        photo_urls = []

        for i, photo in enumerate(photos[:3]):
            photo_url = self.upload_to_supabase(photo, request.user.uid)
            photo_urls.append(photo_url)
        
        for i, photo_url in enumerate(photo_urls, 1):
            ad_data[f'photo_{i}'] = photo_url

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
    
    def perform_destroy(self, instance):
        self.delete_photos_from_supabase(instance)
        instance.delete()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        # Delete old photos and add new ones on update
        self.delete_photos_from_supabase(instance)

        for i in range(1, 4):
            setattr(instance, f'photo_{i}', None)
        
        photos = request.FILES.getlist('photos')
        photo_urls = []
        for i, photo in enumerate(photos[:3]):
            photo_url = self.upload_to_supabase(photo, request.user.uid)
            photo_urls.append(photo_url)
    
        ad_data_json = request.data.get('ad_data', {})
        request_data = json.loads(ad_data_json)

        for i, photo_url in enumerate(photo_urls, 1):
            request_data[f'photo_{i}'] = photo_url
        
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

    def delete_photos_from_supabase(self, ad_instance):
        photos_to_delete = []

        # Check each photo field and extract the filename
        for i in range(1, 4):
            photo_url = getattr(ad_instance, f'photo_{i}', None)

            if photo_url:
                # Extract filename from the full public URL and remove query string
                filename = photo_url.split('/')[-1].split('?')[0]  # Remove everything after '?'
                photos_to_delete.append(filename)  
        
        # Delete photos from Supabase storage
        for photo_path in photos_to_delete:
            # Construct the full storage path
            full_path = f"ad-photos/{photo_path}"
            # Try the deletion
            result = supabase.storage.from_('ad-photos').remove([full_path])
          
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_ads_by_type(request, ad_type_id):
    ads = Ad.objects.filter(ad_type_id=ad_type_id, is_active=True)
    serializer = AdSerializer(ads, many=True)
    return Response({
        'success': True,
        'data': serializer.data
    })

    


