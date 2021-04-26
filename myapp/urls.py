from django.conf.urls import url
from django.urls import path, include
from . import views

urlpatterns = [
    url(r'^$', views.LoginTemplate.as_view(), name='login'),
    path('index', views.HomeTemplate.as_view(), name='index'),

    path('listuser', views.UserDatatableView.as_view(), name='listuser'),
    path('user', views.UserTemplate.as_view(), name='user'),
    path('edituser', views.EditUser.as_view(), name='edituser'),
    path('deleteuser', views.DeleteUser.as_view(), name='deleteuser'),

    path('listproduct', views.ProductDatatableView.as_view(), name='listproduct'),
    path('product', views.ProductTemplate.as_view(), name='product'),
    path('editproduct', views.EditProduct.as_view(), name='editproduct'),
    path('deleteproduct', views.DeleteProduct.as_view(), name='deleteproduct'),

    path('listrole', views.RoleDatatableView.as_view(), name='listrole'),
    path('role', views.RoleTemplate.as_view(), name='role'),
    path('editrole', views.EditRole.as_view(), name='editrole'),
    path('deleterole', views.DeleteRole.as_view(), name='deleterole'),

    path('listpermission', views.PermissionDatatableView.as_view(), name='listpermission'),
    path('permission', views.PermissionTemplate.as_view(), name='permission'),
    path('editpermission', views.EditPermission.as_view(), name='editpermission'),
    path('deletepermission', views.DeletePermission.as_view(), name='deletepermission'),

    path('listassignpermission', views.AssignPermissionDatatableView.as_view(), name='listassignpermission'),
    path('<int:role_id>/assignpermission/', views.AssignPermissionTemplate.as_view(), name='assignpermission'),
    path('editassignpermission', views.EditAssignPermission.as_view(), name='editassignpermission'),

]