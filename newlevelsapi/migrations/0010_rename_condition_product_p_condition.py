# Generated by Django 4.1.13 on 2024-05-12 10:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('newlevelsapi', '0009_alter_product_price'),
    ]

    operations = [
        migrations.RenameField(
            model_name='product',
            old_name='condition',
            new_name='p_condition',
        ),
    ]
