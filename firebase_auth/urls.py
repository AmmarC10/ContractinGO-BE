from django.urls import path
from .views import SignUpView, GoogleSignInView

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='User Sign Up'),
    path('gmailSignUp/', GoogleSignInView.as_view(), name='Sign in with gmail')
]