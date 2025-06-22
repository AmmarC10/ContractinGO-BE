from rest_framework.views import APIView
from rest_framework.response import Response
from firebase_admin import auth
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import render
from .models import User
from .serializers import UserSerializer
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
