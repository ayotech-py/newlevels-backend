# Generated by Django 4.1.13 on 2024-05-12 08:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('newlevelsapi', '0007_product_approved_product_condition_product_featured'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='condition',
            field=models.CharField(default='Brand New', max_length=50),
        ),
    ]
