# Generated by Django 3.1.7 on 2021-04-20 09:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0004_role_permission'),
    ]

    operations = [
        migrations.AlterField(
            model_name='role',
            name='permission',
            field=models.CharField(default=2, max_length=200),
            preserve_default=False,
        ),
    ]
