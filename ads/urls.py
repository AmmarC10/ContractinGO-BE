from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AdViewSet, get_ads_by_type

router = DefaultRouter()
router.register(r'', AdViewSet, basename='ad')

urlpatterns = [
    path('', include(router.urls)),
    path('get_ads_by_type/<int:ad_type_id>/', get_ads_by_type, name='ads-by-type'),
]