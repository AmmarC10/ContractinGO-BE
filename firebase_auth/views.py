from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from firebase_admin import auth
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import render
from .models import User
from .serializers import UserSerializer
from contractingo.supabase_client import supabase
import uuid
import json

# Create your views here.

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

            user = auth.create_user(
                email=email,
                password=password,
                display_name=display_name,
            )

            User.objects.get_or_create(
                uid=user.uid,
                email=user.email,
                profile_photo=user.photo_url,
                name=display_name
            )

            custom_token = auth.create_custom_token(user.uid)

            return Response({
                'success': True,
                'data': {
                    'uid': user.uid,
                    'email': user.email,
                    'displayName': user.display_name,
                    'token': custom_token.decode('utf-8')
                }
            }, status = 201);

        except auth.EmailAlreadyExistsError:
            return Response({
                'success': False,
                'error': 'Email already exists'
            }, status= 400)    
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class GoogleSignInView(APIView):
    def post(self, request):
        try:
            data = json.loads(request.body)
            id_token = data.get('token') 

            try:
                decoded_token = auth.verify_id_token(id_token)
                uid = decoded_token['uid']
            except auth.InvalidIdTokenError:
                return Response({
                    'success': False,
                    'error': 'Invalid authentication token'
                }, status=400)

            try:
                user = auth.get_user(uid)
                is_new_user = False
            except auth.UserNotFoundError:
                user = auth.create_user(
                    uid=uid,
                    email=decoded_token.get('email'),
                    display_name=decoded_token.get('name'),
                )
                is_new_user = True

            User.objects.get_or_create(
                uid=user.uid,
                email=user.email,
                profile_photo=user.photo_url,
                name=decoded_token.get('name')
            )
            custom_token = auth.create_custom_token(uid)
            
            return Response({
                'success': True,
                'data': {
                    'uid': user.uid,
                    'email': user.email,
                    'displayName': user.display_name,
                    'token': custom_token.decode('utf-8'),
                    'isNewUser': is_new_user
                }
            }, status=200)

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class SignInView(APIView):
    def post(self, request):
        try: 
            data = json.loads (request.body)
            email = data.get('email')
            password = data.get('password')

            user = auth.get_user_by_email(email)

            custom_token = auth.create_custom_token(user.uid)

            return Response({
                'success': True,
                'data': {
                    'uid': user.uid,
                    'email': user.email,
                    'displayName': user.display_name,
                    'token': custom_token.decode('utf-8')
                }
            }, status=200)

        except auth.UserNotFoundError:
            return Response({
                'success': False,
                'error': 'User Not Found'
            }, status=400)

        
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class GetUser(APIView):
    def get(self, request):
        uid = request.GET.get('uid')
        if not uid:
            return Response({'success': False, 'error': 'UID is required'}, status = 400)
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
class ChangePassword(APIView):
    def post(self, request):
        try:
            data = json.loads(request.body)
            uid = data.get('uid')
            newPassword = data.get('newPassword')

            auth.update_user(uid, password=newPassword)
            return Response({
                'success': True,
                'message': 'Password Updated Successfully'
            }, status=200)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status = 500)

@method_decorator(csrf_exempt, name='dispatch')
class UploadProfilePhoto(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        uid = request.data.get('uid')
        file_obj = request.FILES.get('profile_photo')

        if not uid:
            return Response({'success': False, 'error': 'UID is required'}, status=400)

        try:
            # Generate a unique file name
            filename = f"{uid}_{uuid.uuid4()}.jpg"
            filePath = f"profile_photos/{filename}"

            result = supabase.storage.from_('profile-photos').upload(path=filePath, file=file_obj.read(), file_options={"content-type": file_obj.content_type})         

            photo_url = f"{supabase.storage.from_('profile-photos').get_public_url(filePath)}"
            auth.update_user(uid, photo_url = photo_url)
            
            user = User.objects.get(uid=uid)
            user.profile_photo = photo_url
            user.save()

            return Response({'success': True, 'message': 'Photo Successfully Updated'}, status=200)
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=500) 