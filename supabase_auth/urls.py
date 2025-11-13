from django.urls import path
from .views import (
    SignUpView, 
    GoogleSignInView, 
    SignInView, 
    GetUser, 
    UpdateUserByUID, 
    RequestPasswordReset,
    UploadProfilePhoto, 
    GetUserById
)

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='User Sign Up'),
    path('gmailSignUp/', GoogleSignInView.as_view(), name='Sign in with gmail'),
    path('login/', SignInView.as_view(), name="User Sign In"),
    path('user/', GetUser.as_view(), name="Get User"),
    path('updateUser/', UpdateUserByUID.as_view(), name="Update User"),
    path('requestPasswordReset/', RequestPasswordReset.as_view(), name="Request Password Reset"),
    path('uploadProfilePhoto/', UploadProfilePhoto.as_view(), name="Upload Profile Photo"),
    path('getUserById/<int:id>/', GetUserById.as_view(), name="Get User By ID")
]