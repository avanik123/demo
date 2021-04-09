from django.urls import path
from . import views

urlpatterns = [
    path('', views.index.as_view(), name='index'),
    path('product', views.ProductList.as_view(), name='productlist'),
    # path('products', views.ListProduct.as_view(), name='listproduct'),
    # path('product/<int:pk>', views.ProductDetail.as_view(), name='productdetail'),
]