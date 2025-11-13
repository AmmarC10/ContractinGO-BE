from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('supabase_auth/', include('supabase_auth.urls')),
    path('api/ads/', include('ads.urls')),
    path('api/messaging/', include('messaging.urls')),
]
