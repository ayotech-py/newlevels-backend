#from djongo import models
from django.db import models
from django.contrib.auth.models import User, auth
import uuid

class Jwt(models.Model):
    user = models.OneToOneField(
        User, related_name="login_user", on_delete=models.CASCADE
    )
    access = models.TextField()
    refresh = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{User.objects.get(id=self.user.id)}"

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, null=True)
    location = models.CharField(max_length=255, null=True)
    profile_image = models.ImageField(upload_to="profile_images/", default="no-profile.png")

    def __str__(self):
        return f"{self.name}"

class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="product_images/", default="no-product-img.png")
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=0)
    category = models.CharField(max_length=255)
    featured = models.BooleanField(default=False)
    approved = models.BooleanField(default=False)
    condition = models.CharField(max_length=50, default='Brand New')

    def __str__(self):
        return f"{Customer.objects.get(id=self.customer.id).name} - {self.title}"