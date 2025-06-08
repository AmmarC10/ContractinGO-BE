from django.urls import path
from .views import SignUpView

urlpatterns = [
    path('test/', SignUpView.as_view(), name='test_firebase')
]