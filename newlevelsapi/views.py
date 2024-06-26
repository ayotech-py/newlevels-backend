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
from django.db.models import Q
from rest_framework.views import APIView
from .api_key_auth import ApiKeyAuthentication
from .authentication import Authentication
from rest_framework.permissions import IsAuthenticated
from django.core.files.base import ContentFile
from django.contrib.auth.hashers import make_password
import pusher
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
import json
from rest_framework import status
from django.db.models import OuterRef, Subquery
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.utils.timezone import now
from decimal import Decimal
from .load_data import load_users




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
            if self.request.method == 'DELETE':
                return queryset
            queryset = queryset.filter(approved__in=[True]).order_by('-featured')
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
            product.image = f'https://res.cloudinary.com/di040wc0d/image/upload/v1/{product.image}'
            product_data = vars(product)
            product_details = '\n'.join([f"{key}: {value}" for key, value in product_data.items()])
            
            send_mail(
                'New Product Posted',
                f'Customer: {product.customer.name}\nProduct Details:\n{product_details}\nClick the link to approve product: https://newlevels-backend.vercel.app/api/approve/{product.unique_token}/\nClick the link to feature product: https://newlevels-backend.vercel.app/api/feature/{product.unique_token}/',
                settings.EMAIL_HOST_USER,
                [settings.EMAIL_HOST_USER],
                fail_silently=False,
            )
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
            product.approved = False
            product.image = image
            product.save()
        except Exception as e:
            product.title = data['title']
            product.description = data['description']
            product.category = data['category']
            product.price = data['price']
            product.condition = data['condition']
            product.approved = False
            product.save()

            product.image = f'https://res.cloudinary.com/di040wc0d/image/upload/v1/{product.image}'
            product_data = vars(product)
            product_details = '\n'.join([f"{key}: {value}" for key, value in product_data.items()])
            
            send_mail(
                'Product Update',
                f'Customer: {product.customer.name}\nProduct Details:\n{product_details}\nClick the link to approve product: https://newlevels-backend.vercel.app/api/approve/{product.unique_token}/\nClick the link to feature product: https://newlevels-backend.vercel.app/api/feature/{product.unique_token}/',
                settings.EMAIL_HOST_USER,
                [settings.EMAIL_HOST_USER],
                fail_silently=False,
            )
        return Response({"message": "Ads successfully Updated!", 'product': ProductSerializer(product).data})

class ApproveProduct(APIView):
    def get(self, request, unique_token):
        try:
            product = Product.objects.get(unique_token=unique_token)
        except Product.DoesNotExist:
            return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        
        product.approved = True
        product.save()
        return Response({"message": "Product approved successfully."}, status=status.HTTP_200_OK)

class FeatureProduct(APIView):
    def get(self, request, unique_token):
        try:
            product = Product.objects.get(unique_token=unique_token)
        except Product.DoesNotExist:
            return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        
        product.featured = True
        product.save()
        return Response({"message": "Product featured successfully."}, status=status.HTTP_200_OK)

class CustomerViewSet(ModelViewSet):
    authentication_classes = [ApiKeyAuthentication]

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

def chat_message_filter(customer):
    chat_rooms_member1 = ChatRoom.objects.filter(member1=customer)
    chat_rooms_member2 = ChatRoom.objects.filter(member2=customer)    
    chat_room_ids_member1 = chat_rooms_member1.values_list('id', flat=True)
    chat_room_ids_member2 = chat_rooms_member2.values_list('id', flat=True)    
    chat_room_ids = list(chat_room_ids_member1) + list(chat_room_ids_member2)    
    chat_messages = Message.objects.filter(chat_room__id__in=chat_room_ids)
    return chat_message

def get_chat_rooms_for_customer(customer):
    chat_rooms = ChatRoom.objects.filter(
        Q(member1=customer) | Q(member2=customer)
    )
    return chat_rooms

def order_chat_rooms_by_latest_message(chat_rooms):
    return sorted(chat_rooms, key=lambda x: x.latest_message_time, reverse=True)


def annotate_chat_rooms_with_latest_message(chat_rooms):
    chat_rooms_with_latest_message = []
    for chat_room in chat_rooms:
        latest_message = Message.objects.filter(chat_room=chat_room).order_by('-timestamp').first()
        latest_message_time = latest_message.timestamp if latest_message else now()
        chat_room.latest_message_time = latest_message_time
        chat_rooms_with_latest_message.append(chat_room)
    return chat_rooms_with_latest_message


class CustomerLoginView(APIView):
    authentication_classes = [ApiKeyAuthentication]

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

        
        """ chatrooms = ChatRoom.objects.filter(Q(member1=customer) | Q(member2=customer)).annotate(
            latest_message_time=Subquery(latest_message.values('timestamp')[:1])
        ).order_by('-latest_message_time') """

        #chat_messages = chat_message_filter(customer.id)

        latest_message = Message.objects.filter(chat_room=OuterRef('pk')).order_by('-timestamp')

        
        chat_rooms = get_chat_rooms_for_customer(customer.id)
        chat_rooms = annotate_chat_rooms_with_latest_message(chat_rooms)  
        chat_rooms = order_chat_rooms_by_latest_message(chat_rooms)


        serialized_product = ProductSerializer(product, many=True)
        serialized_customer = CustomerSerializer(customer)
        serialized_chat = MessageSerializer(chat_messages, many=True)
        serialized_chatroom = ChatRoomSerializer(chat_rooms, many=True)


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

        latest_message = Message.objects.filter(chat_room=OuterRef('pk')).order_by('-timestamp')

        """ chatrooms = ChatRoom.objects.filter(Q(member1=customer) | Q(member2=customer)).annotate(
            latest_message_time=Subquery(latest_message.values('timestamp')[:1])
        ).order_by('-latest_message_time') """

        chat_rooms = get_chat_rooms_for_customer(customer)
        chat_rooms = annotate_chat_rooms_with_latest_message(chat_rooms)  
        chat_rooms = order_chat_rooms_by_latest_message(chat_rooms)

        serialized_product = ProductSerializer(product, many=True)
        serialized_customer = CustomerSerializer(customer)
        serialized_chat = MessageSerializer(chat_messages, many=True)
        serialized_chatroom = ChatRoomSerializer(chat_rooms, many=True)

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

            latest_message = Message.objects.filter(chat_room=OuterRef('pk')).order_by('-timestamp')

            chatrooms = ChatRoom.objects.filter(Q(member1=customer) | Q(member2=customer))
            chatrooms = annotate_chat_rooms_with_latest_message(chatrooms)
            chatrooms = order_chat_rooms_by_latest_message(chatrooms)

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
            print(e)
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
        product = ''
        if "product_id" in data:
            product = Product.objects.get(id=data['product_id'])
            member2 = product.customer
        else:
            member2 = Customer.objects.get(email=data['customer'])
            product = None
        
        try:
            check_chatroom = ChatRoom.objects.filter(Q(member1=member1) & Q(member2=member2) | Q(member1=member2) & Q(member2=member1))
            if len(list(check_chatroom)) > 0:
                last_chatroom = check_chatroom.last()
                last_chatroom.product = product
                Message.objects.create(chat_room=last_chatroom, sender=member1, content=message).save()
                last_chatroom.save()
            else:
                chatroom = ChatRoom.objects.create(member1=member1, member2=member2, product=product)
                chatroom.save()
                chat_message = Message.objects.create(chat_room=chatroom, sender=member1, content=message)
                chat_message.save()

            chat_messages = Message.objects.filter(Q(chat_room__member1=member1.id) | Q(chat_room__member2=member1.id))

            latest_message = Message.objects.filter(chat_room=OuterRef('pk')).order_by('-timestamp')

            chatrooms = ChatRoom.objects.filter(Q(member1=member1) | Q(member2=member1))
            chatrooms = annotate_chat_rooms_with_latest_message(chatrooms)  
            chatrooms = order_chat_rooms_by_latest_message(chatrooms)

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
    permission_classes = [IsAuthenticated]

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


class PasswordResetRequestView(APIView):
    def post(self, request):
        email = request.data.get('email')
        try:
            user = User.objects.get(username=email)
        except User.DoesNotExist:
            return Response({'message': 'User with this email does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_link = request.build_absolute_uri(reverse('password_reset_confirm', args=[uid, token]))

        old_base_url = 'https://newlevels-backend.vercel.app/api/password_reset_confirm/'
        new_base_url = 'https://newlevels-kappa.vercel.app/auth/reset-password/'

        send_mail(
            'Password Reset Request',
            f'Click the link to reset your password: {reset_link.replace(old_base_url, new_base_url)}',
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )

        return Response({'message': 'Password reset link sent to your email'}, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    def post(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            password = request.data.get('password')
            user.set_password(password)
            user.save()
            return Response({'message': 'Password has been reset successfully!'}, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'Invalid link'}, status=status.HTTP_400_BAD_REQUEST)