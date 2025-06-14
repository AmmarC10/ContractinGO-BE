from rest_framework.views import APIView
from rest_framework.response import Response
from firebase_admin import auth
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import render
import json
import logging

logger = logging.getLogger(__name__)

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
                display_name=display_name
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

