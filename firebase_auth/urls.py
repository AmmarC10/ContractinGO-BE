from django.urls import path
from .views import SignUpView, GoogleSignInView, SignInView

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='User Sign Up'),
    path('gmailSignUp/', GoogleSignInView.as_view(), name='Sign in with gmail'),
    path('login/', SignInView.as_view(), name="User Sign In" )
]