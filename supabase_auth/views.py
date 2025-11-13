import json
import uuid
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from contractingo.supabase_client import supabase
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from .models import User
from .serializers import UserSerializer

@method_decorator(csrf_exempt, name='dispatch')
class SignUpView(APIView):
    def post(self, request):
        try:
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')
            first_name = data.get('firstName')
            last_name = data.get('lastName')
            display_name = f"{first_name} {last_name}"

            auth_response = supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "display_name": display_name,
                        "first_name": first_name,
                        "last_name": last_name
                    }
                }
            })

            if not auth_response.user:
                return Response({
                    'success': False,
                    'error': auth_response.error.message
                }, status=400)
            
            user, created = User.objects.get_or_create(
                uid=auth_response.user.id,
                defaults={
                    'email': email,
                    'name': display_name,
                    'profile_photo': None
                }
            )

            return Response({
                'success': True,
                'data': {
                    'uid': auth_response.user.id,
                    'email': email,
                    'displayName': display_name,
                    'token': auth_response.session.access_token if auth_response.session else ''
                }
            }, status=201)
            
        except Exception as e:
            error_msg = str(e)
            if 'already registered' in error_msg.lower():
                return Response({
                    'success': False,
                    'error': 'Email already registered'
                }, status=400)
            return Response({
                'success': False,
                'error': error_msg
            }, status=400)
    
@method_decorator(csrf_exempt, name='dispatch')
class SignInView(APIView):
    def post(self, request):
        try:
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')

            auth_response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            if not auth_response.user:
                return Response({
                    'success': False,
                    'error': 'Invalid credentials'
                }, status=400)

            user, created = User.objects.get_or_create(
                uid=auth_response.user.id,
                defaults={
                    'email': auth_response.user.email,
                    'name': auth_response.user.user_metadata.get('display_name', email)
                }
            )

            return Response({
                'success': True,
                'data': {
                    'uid': auth_response.user.id,
                    'email': auth_response.user.email,
                    'displayName': user.name,
                    'token': auth_response.session.access_token if auth_response.session else ''
                }
            }, status=200)
        except Exception as e:
            error_msg = str(e)
            if 'invalid credentials' in error_msg.lower():
                return Response({
                    'success': False,
                    'error': 'Invalid credentials'
                }, status=400)
            return Response({
                'success': False,
                'error': error_msg
            }, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class GoogleSignInView(APIView):
    def post(self, request):
        try:
            data = json.loads(request.body)
            token = data.get('token')

            if not token:
                return Response({
                    'success': False,
                    'error': 'Token is required'
                }, status=400)
            
            # Verify token and user in supabase
            user_response = supabase.auth.get_user(token)

            if not user_response.user:
                return Response({
                    'success': False,
                    'error': 'Invalid token'
                }, status=400)

            supabase_user = user_response.user
            display_name = supabase_user.user_metadata.get('full_name', supabase_user.email)

            # Get or create user in Django database
            user, created = User.objects.get_or_create(
                uid=supabase_user.id,
                defaults={
                    'email': supabase_user.email,
                    'name': display_name,
                    'profile_photo': supabase_user.user_metadata.get('avatar_url')
                }
            )

            # Update profile photo if it changed
            if not created and supabase_user.user_metadata.get('avatar_url'):
                user.profile_photo = supabase_user.user_metadata.get('avatar_url')
                user.save()
            
            return Response({
                'success': True,
                'data': {
                    'uid': user.uid,
                    'email': user.email,
                    'displayName': user.name,
                    'token': token,
                    'isNewUser': created
                }
            }, status=200)

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class GetUser(APIView):
    def get(self, request):
        uid = request.GET.get('uid')
        if not uid:
            return Response({'success': False, 'error': 'UID is required'}, status=400)
        try:
            user = User.objects.get(uid=uid)
            userSerializer = UserSerializer(user)
            return Response({
                'success': True,
                'data': userSerializer.data
            }, status=200)
        except User.DoesNotExist:
            return Response({'success': False, 'error': 'User Not Found'}, status=404)

@method_decorator(csrf_exempt, name='dispatch')
class UpdateUserByUID(APIView):
    def post(self, request):
        try:
            data = json.loads(request.body)
            uid = data.get('uid')

            if not uid:
                return Response({
                    'success': False,
                    'error': 'UID is required'
                }, status=400)
            
            try:
                user = User.objects.get(uid=uid)
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'User Not Found'
                }, status=404)

            if 'name' in data:
                user.name = data['name']
            if 'phone_number' in data:
                user.phone_number = data['phone_number']
            
            user.save()
            user_serializer = UserSerializer(user)
            return Response({
                'success': True,
                'data': user_serializer.data
            }, status=200)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class RequestPasswordReset(APIView):
    def post(self, request):
        data = json.loads(request.body)
        email = data.get('email')

        if not email:
            return Response({
                'success': False,
                'error': 'Email required'
            }, status=400)

        # send password reset email
        supabase.auth.reset_password_email(email)

        return Response({
                'success': True,
                'message': 'Password reset email sent'
            }, status=200)

@method_decorator(csrf_exempt, name='dispatch')
class UploadProfilePhoto(APIView):
    parser_classes = (MultiPartParser, FormParser)
    def post(self, request):
        uid = request.data.get('uid')
        file_obj = request.FILES.get('profile_photo')

        if not uid:
            return Response({
                'success': False,
                'error': 'UID is required'
            }, status=400)
        
        if not file_obj:
            return Response({
                'success': False,
                'error': 'Profile photo is required'
            }, status=400)
        
        try:
            # Generate a unique file name
            filename = f"{uid}_{uuid.uuid4()}.jpg"
            filePath = f"profile_photos/{filename}"

            result = supabase.storage.from_('profile-photos').upload(
                path=filePath, 
                file=file_obj.read(),
                file_options={"content-type": file_obj.content_type}
            )

            # Get public URl
            photo_url = supabase.storage.from_('profile-photos').get_public_url(filePath)

            # Update user 
            user = User.objects.get(uid=uid)
            user.profile_photo = photo_url
            user.save()

            return Response({
                'success': True, 
                'message': 'Photo Successfully Updated',
                'photo_url': photo_url
            }, status=200)
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=500)

class GetUserById(APIView):
    def get(self, request, id):
        try:
            user = User.objects.get(id=id)
            user_serializer = UserSerializer(user)
            return Response({
                'success': True,
                'data': user_serializer.data
            }, status=200)
        except User.DoesNotExist:
            return Response({'success': False, 'error': 'User Not Found'}, status=404)
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=500)