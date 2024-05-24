from rest_framework import serializers
from .models import *

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer()
    class Meta:
        model = Product
        exclude = ['unique_token']

class CustomerLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

class ChatRoomSerializer(serializers.ModelSerializer):
    product = ProductSerializer()
    member1 = CustomerSerializer()
    member2 = CustomerSerializer()
    class Meta:
        model = ChatRoom
        fields = '__all__'

class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Message
        fields = '__all__'