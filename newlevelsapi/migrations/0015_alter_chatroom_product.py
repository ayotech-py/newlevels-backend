# Generated by Django 4.2 on 2024-05-20 09:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('newlevelsapi', '0014_alter_customer_profile_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chatroom',
            name='product',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='newlevelsapi.product'),
        ),
    ]
