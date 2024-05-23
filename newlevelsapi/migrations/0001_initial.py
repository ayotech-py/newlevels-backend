# Generated by Django 4.1.13 on 2024-05-23 16:32

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ChatRoom',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('phone', models.CharField(max_length=20, null=True)),
                ('location', models.CharField(max_length=255, null=True)),
                ('profile_image', models.ImageField(default='/v1/no-profile.png', upload_to='profile_images/')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('image', models.ImageField(default='no-product-img.png', upload_to='product_images/')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('price', models.DecimalField(decimal_places=0, max_digits=10)),
                ('category', models.CharField(max_length=255)),
                ('featured', models.BooleanField(default=False)),
                ('approved', models.BooleanField(default=False)),
                ('condition', models.CharField(default='Brand New', max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='newlevelsapi.customer')),
            ],
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('content', models.TextField()),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('chat_room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='newlevelsapi.chatroom')),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='newlevelsapi.customer')),
            ],
        ),
        migrations.CreateModel(
            name='Jwt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('access', models.TextField()),
                ('refresh', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='login_user', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='chatroom',
            name='member1',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chatrooms_member1', to='newlevelsapi.customer'),
        ),
        migrations.AddField(
            model_name='chatroom',
            name='member2',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chatrooms_member2', to='newlevelsapi.customer'),
        ),
        migrations.AddField(
            model_name='chatroom',
            name='product',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='newlevelsapi.product'),
        ),
    ]