from django.urls import path
from .views import SignUpView, GoogleSignInView, SignInView, GetUser, UpdateUserByUID

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='User Sign Up'),
    path('gmailSignUp/', GoogleSignInView.as_view(), name='Sign in with gmail'),
    path('login/', SignInView.as_view(), name="User Sign In" ),
    path('user/', GetUser.as_view(), name="Get User"),
    path('updateUser/', UpdateUserByUID.as_view(), name="Update User")
]