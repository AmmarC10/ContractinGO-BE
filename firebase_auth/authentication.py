from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from firebase_admin import auth
from .models import User

class FirebaseAuthentication(BaseAuthentication):
    def authenticate(self, request):
        # Get the Firebase token from the Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header:
            return None
        
        # Extract the token (format: "Bearer <token>")
        try:
            token = auth_header.split(' ')[1]
        except IndexError:
            return None
        
        try:
            # Verify the Firebase token
            decoded_token = auth.verify_id_token(token)
            uid = decoded_token['uid']
            
            # Get the user
            user = User.objects.get(uid=uid)
            
            return (user, None)
            
        except Exception as e:
            raise AuthenticationFailed('Invalid Firebase token') 