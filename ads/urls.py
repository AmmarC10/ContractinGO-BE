from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AdViewSet, AdRequestViewSet, AdReviewViewSet, get_ads_by_type, get_pending_requests_count, get_all_cities, search_ads

router = DefaultRouter()
router.register(r'', AdViewSet, basename='ad')
router.register(r'requests', AdRequestViewSet, basename='ad-request')
router.register(r'reviews', AdReviewViewSet, basename='review')

urlpatterns = [
    path('search/', search_ads, name='search-ads'),
    path('cities/', get_all_cities, name='all-cities'),
    path('pending_requests_count/', get_pending_requests_count, name='pending-requests-count'),
    path('get_ads_by_type/<int:ad_type_id>/', get_ads_by_type, name='ads-by-type'),
    path('', include(router.urls)),
]