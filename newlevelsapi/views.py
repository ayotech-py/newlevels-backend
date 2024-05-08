from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from .serializers import *
import base64
from django.conf import settings
import jwt
from datetime import datetime, timedelta
import random
import string
from django.contrib.auth import authenticate
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from django.db.models import Q
from rest_framework.decorators import action
from rest_framework.views import APIView
from .api_key_auth import ApiKeyAuthentication
from .authentication import Authentication
from rest_framework.permissions import IsAuthenticated
from django.forms.models import model_to_dict
from django.core.files.base import ContentFile
from django.contrib.auth.hashers import make_password

def get_rand(length):
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))

def get_access_token(payload):
    return jwt.encode(
        {"exp": datetime.now() + timedelta(minutes=1000), **payload},
        settings.SECRET_KEY,
        algorithm="HS256",
    )


def get_refresh_token():
    return jwt.encode(
        {"exp": datetime.now() + timedelta(days=365), "data": get_rand(10)},
        settings.SECRET_KEY,
        algorithm="HS256",
    )


def convertImage(image):
    name = "photo"
    format, imgstr = image.split(";base64,")
    ext = format.split("/")[-1]
    image_file = ContentFile(base64.b64decode(imgstr), name=f"{name}.{ext}")
    return image_file

class ProductViewSet(ModelViewSet):
    serializer_class = ProductSerializer
    queryset = Product.objects.all()

class CustomerViewSet(ModelViewSet):
    #authentication_classes = [ApiKeyAuthentication]
    
    serializer_class = CustomerSerializer
    queryset = Customer.objects.all()

    def create(self, request, *args, **kwargs):
        data = request.data
        serialized_data = self.serializer_class(data=data)        
        if len(list(User.objects.filter(email=data["email"]))) > 0:
            return Response({"message": "Email address already exist"}, status=400)
        try:
            user = User.objects.create(
                username=serialized_data.initial_data["email"],
                email=serialized_data.initial_data["email"],
                password=make_password(data["password"])
            )
            serialized_data.initial_data.pop("password", None)
            Customer.objects.create(**serialized_data.initial_data, user=user)
            user.save()
            return Response(
                {"message": "Your account have been successfully created"},
                status=200,
            )
        except Exception as e:
            return Response({"message": "An error occurred"}, status=400)

class CustomerLoginView(APIView):
    #authentication_classes = [ApiKeyAuthentication]

    serializer_class = CustomerLoginSerializer

    def post(self, request):
        data = request.data
        serializer = self.serializer_class(data=data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response({"message": "Invalid email address"}, status=400)

        print(serializer.validated_data)
        user = authenticate(
            username=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )

        if not user:
            return Response({"message": "invalid email or password"}, status=400)

        check_user = Customer.objects.get(user_id=user.id)
        print(check_user)

        if not check_user:
            return Response({"message": "invalid emall or password"}, status=400)

        Jwt.objects.filter(user_id=user.pk).delete()

        access = get_access_token({"user_id": user.id})
        refresh = get_refresh_token()

        Jwt.objects.create(user_id=user.id, access=access, refresh=refresh)

        return Response(
            {
                "access": access,
                "refresh": refresh,
                "username": user.username,
                "message": "Login successful!",
            }
        )

class GetCustomerDetails(APIView):
    authentication_classes = [Authentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_id = request.user.id
        user_email = User.objects.get(id=user_id).username
        customer = Customer.objects.get(user=user_id)

        product = Product.objects.filter(customer=customer.id)
        serialized_product = ProductSerializer(product, many=True)
        print(serialized_product.data)
        context = {
            "product": serialized_product.data
        }
        print(context)
        return Response(context)