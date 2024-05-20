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
from asgiref.sync import sync_to_async
import pusher
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
import json
from django.http import JsonResponse
from rest_framework import status


def get_rand(length):
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))

def get_access_token(payload):
    return jwt.encode(
        {"exp": datetime.now() + timedelta(minutes=7200), **payload},
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
    """ authentication_classes = [Authentication]
    permission_classes = [IsAuthenticated] """
    
    serializer_class = ProductSerializer
    queryset = Product.objects.all()

    def get_authenticators(self):
        if self.request.method == 'GET':
            return [ApiKeyAuthentication()]
        return [Authentication()]

    def get_permissions(self):
        if self.request.method == 'GET':
            return []  # No additional permissions for GET requests
        return [IsAuthenticated()]

    def get_queryset(self):
        try:
            queryset = super().get_queryset()
            queryset = queryset.filter(approved=True).order_by('-featured')
            return queryset
        except Exception as e:
            return Response({"message": "Failed to fetch"})

    def create(self, request, *args, **kwargs):
        data = request.data
        user_id = request.user.id
        customer = Customer.objects.get(user=user_id)
        image = convertImage(data['image'])
        data[image] = image
        data['customer'] = customer.id
        try:
            product = Product.objects.create(
                title=data['title'],
                description=data['description'],
                price=data['price'],
                category=data['category'],
                condition=data['condition'],
                image=image,
                customer=customer
            )
            product.save()
            return Response({"message": "Product successfull added!", "product": ProductSerializer(product).data}, status=200)
        except Exception as e:
            return Response({"message": "An error occured"}, status=400)

    def update(self, request, *args, **kwargs):
        data = request.data
        user_id = request.user.id
        customer = Customer.objects.get(user=user_id)
        product = Product.objects.get(id=data['id'])
        try:
            image = convertImage(data['image'])
            product.title = data['title']
            product.description = data['description']
            product.category = data['category']
            product.price = data['price']
            product.condition = data['condition']
            product.image = image
            product.save()
        except Exception as e:
            product.title = data['title']
            product.description = data['description']
            product.category = data['category']
            product.price = data['price']
            product.condition = data['condition']
            product.save()
        return Response({"message": "Ads successfully Updated!", 'product': ProductSerializer(product).data})


class CustomerViewSet(ModelViewSet):
    #authentication_classes = [ApiKeyAuthentication]

    serializer_class = CustomerSerializer
    queryset = Customer.objects.all()

    def create(self, request, *args, **kwargs):
        data = request.data
        serialized_data = self.serializer_class(data=data)        
        if len(list(User.objects.filter(email=data["email"]))) > 0:
            return Response({"message": "Email address already exist"}, status=400)
        elif len(list(User.objects.filter(customer__name=data["name"]))) > 0:
            return Response({"message": "Name already exist"}, status=400)
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

        user = authenticate(
            username=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )

        if not user:
            return Response({"message": "invalid email or password"}, status=400)

        check_user = Customer.objects.get(user_id=user.id)

        if not check_user:
            return Response({"message": "invalid emall or password"}, status=400)

        Jwt.objects.filter(user_id=user.pk).delete()

        access = get_access_token({"user_id": user.id})
        refresh = get_refresh_token()

        Jwt.objects.create(user_id=user.id, access=access, refresh=refresh)

        

        user_email = User.objects.get(id=user.id).username
        customer = Customer.objects.get(user=user.id)
        product = Product.objects.filter(customer=customer.id).order_by('-featured')
        chat_messages = Message.objects.filter(Q(chat_room__member1=customer.id) | Q(chat_room__member2=customer.id))
        chatrooms = ChatRoom.objects.filter(Q(member1=customer) | Q(member2=customer))

        serialized_product = ProductSerializer(product, many=True)
        serialized_customer = CustomerSerializer(customer)
        serialized_chat = MessageSerializer(chat_messages, many=True)
        serialized_chatroom = ChatRoomSerializer(chatrooms, many=True)


        context = {
            "product": serialized_product.data,
            "customer": serialized_customer.data,
            "chats": serialized_chat.data,
            "chat_rooms": serialized_chatroom.data
        }

        return Response(
            {   
                "tokens": {
                    "accessToken": access,
                    "refreshToken": refresh
                },
                "username": user.username,
                "message": "Login successful!",
                "userData": context
            }, status=200
        )

class GetCustomerDetails(APIView):
    authentication_classes = [Authentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        customer = Customer.objects.get(user=user.id)
        product = Product.objects.filter(customer=customer.id).order_by('-featured')
        chat_messages = Message.objects.filter(Q(chat_room__member1=customer.id) | Q(chat_room__member2=customer.id))
        chatrooms = ChatRoom.objects.filter(Q(member1=customer) | Q(member2=customer))

        serialized_product = ProductSerializer(product, many=True)
        serialized_customer = CustomerSerializer(customer)
        serialized_chat = MessageSerializer(chat_messages, many=True)
        serialized_chatroom = ChatRoomSerializer(chatrooms, many=True)

        context = {
            "product": serialized_product.data,
            "customer": serialized_customer.data,
            "chats": serialized_chat.data,
            "chat_rooms": serialized_chatroom.data
        }

        return Response(
            {   
                "userData": context
            }, status=200
        )

class UpdateCustomer(APIView):
    authentication_classes = [Authentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_id = request.user.id
        data = request.data
        customer = Customer.objects.get(user=user_id)

        try:
            image = convertImage(data['image'])
            customer.profile_image = image
        except Exception as e:
            pass
        try:
            request.user.email = data['email']
            request.user.username = data['email']
            customer.name = data['name']
            customer.phone = data['phone']
            customer.email = data['email']
            customer.location = data['location']
            customer.save()
            request.user.save()

            product = Product.objects.filter(customer=customer.id).order_by('-featured')
            chat_messages = Message.objects.filter(Q(chat_room__member1=customer.id) | Q(chat_room__member2=customer.id))
            chatrooms = ChatRoom.objects.filter(Q(member1=customer) | Q(member2=customer))

            serialized_product = ProductSerializer(product, many=True)
            serialized_customer = CustomerSerializer(customer)
            serialized_chat = MessageSerializer(chat_messages, many=True)
            serialized_chatroom = ChatRoomSerializer(chatrooms, many=True)
            context = {
                "product": serialized_product.data,
                "customer": serialized_customer.data,
                "chats": serialized_chat.data,
                "chat_rooms": serialized_chatroom.data
            }

            return Response({"message": "Profile successfully Updated!", "userData": context}, status=200)
        except Exception as e:
            return Response({"message": "An error occured!"}, status=400)

class ChatRoomViewSet(ModelViewSet):
    queryset = ChatRoom.objects.all()
    serializer_class = ChatRoomSerializer
    authentication_classes = [Authentication]
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        data = request.data
        message = data['chat']
        user = request.user
        member1 = Customer.objects.get(user=user.id)
        if "product_id" in data:
            product = Product.objects.get(id=data['product_id'])
            member2 = product.customer
        else:
            member2 = Customer.objects.get(email=data['customer'])
            product = None
        
        try:
            check_chatroom = ChatRoom.objects.filter(Q(member1=member1) & Q(member2=member2) | Q(member1=member2) & Q(member2=member1))
            if check_chatroom.exists():
                last_chatroom = check_chatroom.last()
                last_chatroom.product = product
                last_chatroom.save()
                chat_message = Message.objects.create(chat_room=check_chatroom.last(), sender=member1, content=message)
                chat_message.save()
            else:
                chatroom = ChatRoom.objects.create(member1=member1, member2=member2, product=product)
                chat_message = Message.objects.create(chat_room=chatroom, sender=member1, content=message)
                chat_message.save()
                chatroom.save()

            chat_messages = Message.objects.filter(Q(chat_room__member1=member1.id) | Q(chat_room__member2=member1.id))
            chatrooms = ChatRoom.objects.filter(Q(member1=member1) | Q(member2=member1))

            serialized_chat = MessageSerializer(chat_messages, many=True)
            serialized_chatroom = ChatRoomSerializer(chatrooms, many=True)

            context = {
                "chats": serialized_chat.data,
                "chat_rooms": serialized_chatroom.data
            }
            return Response({"message": "Message successfully sent", "chatData": context}, status=200)
        except Exception as e:
            return Response({"message": "An error occurred"}, status=400)


class MessageViewSet(ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    #permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user.customer)

    def get_queryset(self):
        queryset = super().get_queryset()
        query_params = self.request.query_params

        filters = []

        room_id_params = query_params.get("room_id")
        if room_id_params:
            filters.append(Q(chat_room__id=room_id_params))

        if filters:
            queryset = queryset.filter(Q(*filters))

        return queryset


pusher_client = pusher.Pusher(
  app_id=settings.PUSHER_APP_ID,
  key=settings.PUSHER_KEY,
  secret=settings.PUSHER_SECRET,
  cluster=settings.PUSHER_CLUSTER,
  ssl=True
)

@method_decorator(csrf_exempt, name='dispatch')
class SendMessageView(APIView):
    authentication_classes = [Authentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            room_id = data['room_id']
            sender_email = data['sender']
            content = data['message']
            
            room = get_object_or_404(ChatRoom, id=room_id)
            sender = get_object_or_404(Customer, email=sender_email)
            message = Message.objects.create(chat_room=room, sender=sender, content=content)
            
            pusher_client.trigger(f'chat_{room_id}', 'chat_message', {
                'id': message.id,
                'chat_room': room.id,
                'content': content,
                'sender': sender.email,
                'timestamp': message.timestamp.isoformat()
            })
            
            return Response({'status': 'Message sent'}, status=status.HTTP_201_CREATED)
        except KeyError:
            return Response({'error': 'Invalid request data'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)