# Generated by Django 3.2 on 2021-05-31 11:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0012_alter_permission_deleted'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='permission',
            name='deleted',
        ),
        migrations.AddField(
            model_name='permission',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
