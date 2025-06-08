from rest_framework.views import APIView
from rest_framework.response import Response
from firebase_admin import auth
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import render
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
                display_name=display_name
            )

            custom_token = auth.create_custom_token(user.id)

            return Response({
                'message': 'User Created Successfully'
            }, status = 201)

        except auth.EmailAlreadyExistsError:
            return Response({
                'error': 'Email already exists'
            }, status= 400)    
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=400)

