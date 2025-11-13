from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from jose import jwt, JWTError
import os
from supabase_auth.models import User

class SupabaseAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header:
            return None
        
        try:
            token = auth_header.split(' ')[1]
        except IndexError:
            return None
        
        try:
            jwt_secret = os.getenv('SUPABASE_JWT_SECRET')
            payload = jwt.decode(token, jwt_secret, algorithms=['HS256'], audience='authenticated')
            uid = payload.get('sub')
            email = payload.get('email')
            
            user, created = User.objects.get_or_create(
                uid=uid,
                email=email,
                defaults={
                    'name': payload.get('name'),
                    'profile_photo': payload.get('picture')
                }
            )
            return (user, None)
        except JWTError:
            raise AuthenticationFailed('Invalid token')
        except Exception as e:
            raise AuthenticationFailed('Authentication failed: ' + str(e))
