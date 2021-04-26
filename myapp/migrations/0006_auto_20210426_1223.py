# Generated by Django 3.1.7 on 2021-04-26 06:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0005_auto_20210426_1220'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rolepermission',
            name='permission_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='myapp.permission'),
        ),
        migrations.AlterField(
            model_name='rolepermission',
            name='role_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='myapp.role'),
        ),
    ]
