from django.shortcuts import render
from django.views.generic import TemplateView
from myapp import models
from myapp import serializers
from rest_framework import generics
from rest_framework import status
from django.contrib import messages
from rest_framework.response import Response

# Create your views here.
class LoginTemplate(TemplateView):
    template_name = 'login.html'


class HomeTemplate(TemplateView):
    template_name = 'index.html'


class ProductTemplate(TemplateView):
    queryset = models.Product.objects.all()
    template_name = 'product.html'
    model = models.Product

    def get_context_data(self, **kwargs):
        context = super(ProductTemplate, self).get_context_data(**kwargs)
        context['products'] = models.Product.objects.all()
        return context


class ListProduct(generics.ListCreateAPIView):
    queryset = models.Product.objects.all()
    serializer_class = serializers.ProductSerializer


class ProductDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Product.objects.all()
    serializer_class = serializers.ProductSerializer


class Product(generics.CreateAPIView):
    serializer_class = serializers.ProductSerializer
    model = models.Product

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response({"status": 200, "message": 'created successfully.'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"status": 400, "message": "Fail to create"}, status=status.HTTP_400_BAD_REQUEST)


class ProductPutUpdate(generics.UpdateAPIView):
    serializer_class = serializers.ProductSerializer
    model = models.Product
    lookup_field = 'id'
    http_method_names = ['put']

    def get_queryset(self):
        return self.model.objects.all(id)

    def update(self, request, *args, **kwargs):
        try:
            response = super(ProductPutUpdate, self).update(self, request, *args, **kwargs)
            print(response)
            return Response({'success': True, 'data': response.data})
        except Exception as e:
            print(e)
            return Response({'message': format(e.args[-1]), 'success': False})


class ProductDelete(generics.DestroyAPIView):
    serializer_class = serializers.ProductSerializer
    model = models.Product
    lookup_field = 'id'

    def get_queryset(self):
        return self.model.objects.all()

    def delete(self, request, *args, **kwargs):
        try:
            response = super(ProductDelete, self).delete(request, *args, **kwargs)
            return Response({"status": True, "message": "Product deleted successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({"status": False, "message": "Fail to delete product"}, status=status.HTTP_400_BAD_REQUEST)
