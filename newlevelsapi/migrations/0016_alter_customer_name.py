# Generated by Django 4.2 on 2024-05-20 22:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('newlevelsapi', '0015_alter_chatroom_product'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='name',
            field=models.CharField(max_length=255, unique=True),
        ),
    ]