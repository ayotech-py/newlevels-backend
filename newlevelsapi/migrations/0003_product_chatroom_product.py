# Generated by Django 4.1.13 on 2024-05-24 07:56

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('newlevelsapi', '0002_remove_chatroom_product_delete_product'),
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('image', models.ImageField(default='no-product-img.png', upload_to='product_images/')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('price', models.IntegerField()),
                ('category', models.CharField(max_length=255)),
                ('featured', models.BooleanField(default=False)),
                ('approved', models.BooleanField(default=False)),
                ('condition', models.CharField(default='Brand New', max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('unique_token', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='newlevelsapi.customer')),
            ],
        ),
        migrations.AddField(
            model_name='chatroom',
            name='product',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='newlevelsapi.product'),
        ),
    ]
