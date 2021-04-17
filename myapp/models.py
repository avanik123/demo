from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class Product(models.Model):
    pro_name = models.CharField(max_length=100)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now= True)
    
    def __str__(self):
        return self.pro_name


class Roll(models.Model):
    roll = models.CharField(max_length=200, unique=True)
    permission = models.CharField(max_length=200, unique=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now= True)

    def __str__(self):
        return self.roll

 
class User(AbstractUser): 
    email = models.EmailField(max_length=254, null=False, unique=True)

    def __str__(self):
        return self.email