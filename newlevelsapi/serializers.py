from rest_framework import serializers
from .models import *

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'

class ProductSerializers(serializers.ModelSerializer):
    customer = CustomerSerializer()
    class Meta:
        model = Product
        fields = '__all__'