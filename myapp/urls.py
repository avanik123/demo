from django.urls import path, include
from . import views

urlpatterns = [
    path('listproducts1', views.ProductDatatableView.as_view(), name='listproducts1'),

    path('', views.LoginTemplate.as_view(), name='login'),
    path('index', views.HomeTemplate.as_view(), name='index'),
    path('product', views.ProductTemplate.as_view(), name='product'),

    path('products/<int:pk>', views.ProductDetail.as_view(), name='products'),
    path('createproduct', views.Product.as_view(), name='createproduct'),
    path('updateproduct/<int:id>', views.ProductPutUpdate.as_view(), name='updateproduct'),
    path('deleteproduct/<int:id>', views.ProductDelete.as_view(), name='deleteproduct'),
]