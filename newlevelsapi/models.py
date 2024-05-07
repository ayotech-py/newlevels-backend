from djongo import models
from django.contrib.auth.models import User, auth
import uuid

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    location = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    profile_image = models.ImageField(upload_to="profile_images/", default="no-product-img.png")

class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seller = models.ForeignKey(Customer, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="product_images/", default="no-product-img.png")
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=255)
    
    def __str__(self):
        return self.name
