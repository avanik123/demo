from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class User(AbstractUser): 
    class Meta:
        db_table = "user"

    username = models.CharField(max_length=254, null=False, unique=True)
    email = models.EmailField(max_length=254, null=False, unique=True)

    def __str__(self):
        return self.email


class Product(models.Model):
    class Meta:
        db_table = "product"

    pro_name = models.CharField(max_length=100)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now= True)
    
    def __str__(self):
        return self.pro_name


class Permission(models.Model):
    class Meta:
        db_table = "permission"

    permission = models.CharField(max_length=200)
    method = models.CharField(max_length=200, null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now= True)

    def __str__(self):
        return self.permission


class Role(models.Model):
    class Meta:
        db_table = "role"

    role = models.CharField(max_length=200, unique=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now= True)

    def __str__(self):
        return self.role


class RolePermission(models.Model):
    class Meta:
        db_table = "rolepermission"

    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now= True)
    

class UserRole(models.Model):
    class Meta:
        db_table = "userrole"

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now= True)
