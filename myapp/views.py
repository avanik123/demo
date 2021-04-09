from django.shortcuts import render
from .models import *
from .serializers import *
from rest_framework import generics
from django.views.generic import TemplateView

# Create your views here.
class index(TemplateView):
    template_name = 'index.html'


class ProductList(TemplateView):
    template_name = 'product.html'
    model = Product

    def get_context_data(self, **kwargs):
        context = super(ProductList, self).get_context_data(**kwargs)
        context['products'] = Product.objects.all()
        return context


# class ListProduct(generics.ListCreateAPIView):
#     queryset = Product.objects.all()
#     serializer_class = ProductSerializer


# class ProductDetail(generics.RetrieveUpdateDestroyAPIView):
#     queryset = Product.objects.all()
#     serializer_class = ProductSerializer