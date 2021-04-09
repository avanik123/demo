from django.db import models

# Create your models here.
class Product(models.Model):
    pro_name = models.CharField(max_length=100)

    def __str__(self):
        return self.pro_name