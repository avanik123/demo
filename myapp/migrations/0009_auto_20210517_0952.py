# Generated by Django 3.2 on 2021-05-17 04:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0008_remove_user_role'),
    ]

    operations = [
        migrations.RenameField(
            model_name='rolepermission',
            old_name='permission_id',
            new_name='permission',
        ),
        migrations.RenameField(
            model_name='rolepermission',
            old_name='role_id',
            new_name='role',
        ),
        migrations.RenameField(
            model_name='userrole',
            old_name='role_id',
            new_name='role',
        ),
        migrations.RenameField(
            model_name='userrole',
            old_name='user_id',
            new_name='user',
        ),
    ]
