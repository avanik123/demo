# Generated by Django 3.1.7 on 2021-04-26 05:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0003_auto_20210424_1037'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='RolePermissions',
            new_name='RolePermission',
        ),
    ]