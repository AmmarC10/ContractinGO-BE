from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Ad, AdType, Photo, AdRequest, Review, City
from .serializers import AdSerializer, AdTypeSerializer, AdRequestSerializer, CitySerializer, ReviewSerializer
import uuid
import json
from contractingo.supabase_client import supabase
from django.db import models
from django.db.models import Q, Case, When, IntegerField, Value
from django.core.paginator import Paginator
import re

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

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def request_ad(self, request, pk=None):
        """Allow users to request an ad (not the owner)"""
        ad = self.get_object()
        
        # Check if user is not the ad owner
        if ad.user == request.user:
            return Response({
                'success': False,
                'error': 'You cannot request your own ad'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if request already exists
        existing_request = AdRequest.objects.filter(ad=ad, requester=request.user).first()
        if existing_request:
            return Response({
                'success': False,
                'error': 'You have already requested this ad'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        message = request.data.get('message', '')
        
        ad_request = AdRequest.objects.create(
            ad=ad,
            requester=request.user,
            message=message
        )
        
        serializer = AdRequestSerializer(ad_request)
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def requests(self, request, pk=None):
        """Get all requests for an ad (only visible to ad owner)"""
        ad = self.get_object()
        
        # Only ad owner can see requests
        if ad.user != request.user:
            return Response({
                'success': False,
                'error': 'You can only view requests for your own ads'
            }, status=status.HTTP_403_FORBIDDEN)
        
        requests = AdRequest.objects.filter(ad=ad).order_by('-created_at')
        serializer = AdRequestSerializer(requests, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def my_requests(self, request):
        """Get all requests made by the current user"""
        requests = AdRequest.objects.filter(requester=request.user).order_by('-created_at')
        serializer = AdRequestSerializer(requests, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data
        })

class AdRequestViewSet(viewsets.ModelViewSet):
    serializer_class = AdRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        # Users can see their own requests and requests for their ads
        return AdRequest.objects.filter(
            models.Q(requester=user) | models.Q(ad__user=user)
        ).distinct()
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Accept an ad request (only ad owner)"""
        ad_request = self.get_object()
        
        # Only ad owner can accept
        if ad_request.ad.user != request.user:
            return Response({
                'success': False,
                'error': 'Only the ad owner can accept requests'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if ad_request.status != 'pending':
            return Response({
                'success': False,
                'error': 'This request has already been processed'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        ad_request.status = 'accepted'
        ad_request.save()
        
        serializer = AdRequestSerializer(ad_request)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def decline(self, request, pk=None):
        """Decline an ad request (only ad owner)"""
        ad_request = self.get_object()
        
        # Only ad owner can decline
        if ad_request.ad.user != request.user:
            return Response({
                'success': False,
                'error': 'Only the ad owner can decline requests'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if ad_request.status != 'pending':
            return Response({
                'success': False,
                'error': 'This request has already been processed'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        ad_request.status = 'declined'
        ad_request.save()
        
        serializer = AdRequestSerializer(ad_request)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def start_job(self, request, pk=None):
        """Start the job (only ad owner)"""
        ad_request = self.get_object()
        
        # Only ad owner can start job
        if ad_request.ad.user != request.user:
            return Response({
                'success': False,
                'error': 'Only the ad owner can start the job'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if ad_request.status != 'accepted':
            return Response({
                'success': False,
                'error': 'Job can only be started for accepted requests'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        ad_request.status = 'in_progress'
        ad_request.save()
        
        serializer = AdRequestSerializer(ad_request)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def confirm_completion(self, request, pk=None):
        """Confirm job completion (both parties)"""
        ad_request = self.get_object()
        user_type = request.data.get('user_type')  # 'owner' or 'requester'
        
        if user_type == 'owner' and ad_request.ad.user != request.user:
            return Response({
                'success': False,
                'error': 'Only the ad owner can confirm completion'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if user_type == 'requester' and ad_request.requester != request.user:
            return Response({
                'success': False,
                'error': 'Only the requester can confirm completion'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if ad_request.status != 'in_progress':
            return Response({
                'success': False,
                'error': 'Job must be in progress to confirm completion'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if user_type == 'owner':
            ad_request.owner_confirmed_completion = True
        elif user_type == 'requester':
            ad_request.requester_confirmed_completion = True
        
        ad_request.save()
        
        # If both parties confirmed, mark as completed
        if ad_request.owner_confirmed_completion and ad_request.requester_confirmed_completion:
            ad_request.status = 'completed'
            ad_request.save()
        
        serializer = AdRequestSerializer(ad_request)
        return Response({
            'success': True,
            'data': serializer.data
        })

class AdReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Review.objects.filter(
            models.Q(reviewer=self.request.user) | models.Q(reviewee=self.request.user)
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(reviewer=self.request.user)
    
    @action(detail=False, methods=['post'])
    def create_review(self, request):
        ad_request_id = request.data.get('ad_request_id')
        rating = request.data.get('rating')
        comment = request.data.get('comment', '')

        if not ad_request_id or not rating:
            return Response({
                'success': False,
                'error': 'Ad request ID and rating are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            ad_request = AdRequest.objects.get(id=ad_request_id)
        except AdRequest.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Ad request not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if ad_request.status != 'completed':
            return Response({
                'success': False,
                'error': 'Review can only be created for completed requests'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if hasattr(ad_request, 'review'):
            return Response({
                'success': False,
                'error': 'Review already exists for this ad request'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if ad_request.requester != request.user:
            return Response({
                'success': False,
                'error': 'Only the requester can review this ad'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Create review
        review = Review.objects.create(
            ad_request=ad_request,
            reviewer=request.user,
            reviewee=ad_request.ad.user,
            rating=rating,
            comment=comment
        )

        serializer = ReviewSerializer(review)
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)

    
    @action(detail=False, methods=['get'])
    def my_reviews_given(self, request):
         """Get all reviews given by the current user"""
         reviews = Review.objects.filter(reviewer=request.user).order_by('-created_at')
         serializer = ReviewSerializer(reviews, many=True)
         return Response({
            'success': True,
            'data': serializer.data
         })

    @action(detail=False, methods=['get'])
    def user_reviews(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({
                'success': False,
                'error': 'User ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            reviews = Review.objects.filter(reviewee=user_id).order_by('-created_at')
            serializer = self.get_serializer(reviews, many=True)
            return Response({
                'success': True,
                'data': serializer.data
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def can_review(self, request):
        """Check if user can review a specific ad request"""
        ad_request_id = request.query_params.get('ad_request_id')
        if not ad_request_id:
            return Response({
                'success': False,
                'error': 'ad_request_id parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            ad_request = AdRequest.objects.get(id=ad_request_id)
        except AdRequest.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Ad request not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check conditions for reviewing
        can_review = (
            ad_request.requester == request.user and
            ad_request.status == 'completed' and
            not hasattr(ad_request, 'review')
        )
        
        return Response({
            'success': True,
            'can_review': can_review,
            'reason': 'Can review' if can_review else 'Cannot review - check if you are the requester, request is completed, and no review exists'
        })
          
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_ads_by_type(request, ad_type_id):
    ads = Ad.objects.filter(ad_type_id=ad_type_id, is_active=True)
    serializer = AdSerializer(ads, many=True)
    return Response({
        'success': True,
        'data': serializer.data
    })

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_pending_requests_count(request):
    pending_requests = AdRequest.objects.filter(ad__user=request.user, status='pending').count()
    return Response({
        'success': True,
        'pending_requests': pending_requests
    })

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_all_cities(request):
    cities = City.objects.all().order_by('name')
    serializer = CitySerializer(cities, many=True)
    return Response({
        'success': True,
        'data': serializer.data
    })

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def search_ads(request):
    query = request.GET.get('q', '').strip()
    page_num = int(request.GET.get('page', 1))
    limit = int(request.GET.get('limit', 20))

    if not query:
        return Response({
            'success': False,
            'error': 'Search query is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Parse Query
    query_lower = query.lower()
    search_terms = query_lower.split()

    # Extract location
    location_keywords = None
    location_pattern = r'\b(?:in|near|at)\s+([a-zA-Z\s]+?)(?:\s|$|,)'
    location_match = re.search(location_pattern, query_lower)

    if location_match:
        location_keywords = location_match.group(1).strip()
    else:
        cities = City.objects.all()
        for city in cities:
            if city.name.lower() in query_lower:
                location_keywords = city.name
                break
    
    # Extract service type by matching against ad type names
    service_keywords = None
    ad_types = AdType.objects.all()
    for ad_type in ad_types:
        if ad_type.name.lower() in query_lower:
            service_keywords = ad_type.name
            break
    
    ads = Ad.objects.filter(is_active=True)

    relevance_score = Case(
        # Exact title match: 10 points
        When(title__iexact=query, then=Value(10)),
        # Partial title match: +5 points
        When(title__icontains=query, then=Value(5)),
        default=Value(0),
        output_field=IntegerField()
    )

    # Add ad type score
    if service_keywords:
        relevance_score = relevance_score + Case(
            When(ad_type__name__icontains=service_keywords, then=Value(8)),
            default=Value(0),
            output_field=IntegerField(),
        )
    
    # Add location score
    if location_keywords:
        relevance_score = relevance_score + Case(
            When(location__icontains=location_keywords, then=Value(7)),
            default=Value(0),
            output_field=IntegerField(),
        )
    
    # Add description/tags/skills score
    relevance_score = relevance_score + Case(
        When(description__icontains=query, then=Value(3)),
        default=Value(0),
        output_field=IntegerField(),
    )
    
    relevance_score = relevance_score + Case(
        When(tags__icontains=query, then=Value(3)),
        default=Value(0),
        output_field=IntegerField(),
    )

    relevance_score = relevance_score + Case(
        When(skills__icontains=query, then=Value(3)),
        default=Value(0),
        output_field=IntegerField(),
    )

    # Build final query with OR conditions
    q_objects = Q(title__icontains=query) | Q(description__icontains=query)

    if service_keywords:
        q_objects |= Q(ad_type__name__icontains=service_keywords)
    
    if location_keywords:
        q_objects |= Q(location__icontains=location_keywords)
    
    q_objects |= Q(tags__icontains=query) | Q(skills__icontains=query)

    ads = ads.filter(q_objects).annotate(
        relevance=relevance_score
    ).order_by('-relevance', '-created_at').distinct()

    paginator = Paginator(ads, limit)
    
    try:
        page_obj = paginator.page(page_num)
    except:
        page_obj = paginator.page(1)
        page_num = 1
    
    # Serialize results
    serializer = AdSerializer(page_obj.object_list, many=True)

    return Response({
        'success': True,
        'data': serializer.data,
        'total': paginator.count,
        'current_page': page_num,
        'total_pages': paginator.num_pages,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous()
    })






    


