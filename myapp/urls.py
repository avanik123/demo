from django.conf.urls import url
from django.urls import path, include
from . import views

urlpatterns = [
    url(r'^$', views.LoginTemplate.as_view(), name='login'),
    path('index', views.HomeTemplate.as_view(), name='index'),

    path('listproduct', views.ProductDatatableView.as_view(), name='listproduct'),
    path('product', views.ProductTemplate.as_view(), name='product'),
    path('editproduct', views.EditProduct.as_view(), name='editproduct'),
    path('deleteproduct', views.DeleteProduct.as_view(), name='deleteproduct'),

    path('listroll', views.RollDatatableView.as_view(), name='listroll'),
    path('roll', views.RollTemplate.as_view(), name='roll'),
    path('editroll', views.EditRoll.as_view(), name='editroll'),
    path('deleteroll', views.DeleteRoll.as_view(), name='deleteroll'),

    path('readfile', views.read_file, name='readfile'),
]