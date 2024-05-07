from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from .serializers import *

class ProductViewSet(ModelViewSet):
    serializer_class = ProductSerializers
    queryset = Product.object.all()

class CustomerViewSet(ModelViewSet):
    serializer_class = CustomerSerializers
    queryset = Customer.object.all()

