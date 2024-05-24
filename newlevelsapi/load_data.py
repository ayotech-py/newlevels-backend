import json
import os
from django.contrib.auth.models import User, auth

""" os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'newlevels.settings')
 """
import django
from datetime import datetime
from io import BytesIO
from django.core.files.base import ContentFile
import requests
from django.core.files import File



""" # Set up Django environment
django.setup() """

from .models import *
from django.contrib.auth.hashers import make_password
import base64


def parse_date(date_str):
    return datetime.fromisoformat(date_str.replace('Z', '+00:00'))

def download_image(url):
    response = requests.get(url)
    if response.status_code == 200:
        return ContentFile(response.content)
    return None

""" def download_image(image):
    response = requests.get(image)
    if response.status_code == 200:
        name = "photo"
        format, imgstr = response.content.split(";base64,")
        ext = format.split("/")[-1]
        image_file = ContentFile(base64.b64decode(imgstr), name=f"{name}.{ext}")
        return image_file """

def load_users():
    with open('/home/ayotech/Documents/NewlevelsReact/newlevels-backend/newlevelsapi/06-jobs-api-users.json', 'r') as file:
        users_data = json.load(file)

    with open('/home/ayotech/Documents/NewlevelsReact/newlevels-backend/newlevelsapi/06-jobs-api.products.json', 'r') as file:
        products_data = json.load(file)
        
    for user_data in users_data:
        user = User.objects.create(
                username=user_data['email'],
                email=user_data['email'],
                password=make_password('12345678')
            )
        customer = Customer.objects.create(name=user_data['name'], email=user_data['email'], phone=user_data['phone'], location=user_data['location'], user=user)
        
        print(f"User {user.email} saved.")

        for product_data in products_data:
            if user_data['_id'] == product_data['seller_id']:
                product = Product.objects.create(
                title=product_data['title'],
                description=product_data['description'],
                price=product_data['price'],
                category=product_data['category'],
                condition='Brand New',
                approved=product_data['checked'],
                featured=product_data['featured'],
                customer=customer
                )
                image_url = product_data['image']['url']
                image_content = download_image(image_url)
                if image_content:
                    product.image.save('image', image_content, save=True)
                    print(f"Product {product.title} saved.")
                    product.save()

        customer.save()
        user.save()

