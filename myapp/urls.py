from django.conf.urls import url
from django.urls import path, include
from . import views

urlpatterns = [
    url(r'^$', views.LoginTemplate.as_view(), name='login'),
    path('index/', views.HomeTemplate.as_view(), name='index'),
    url(r'^logout/$', views.logout, name='logout'),

    path('user', views.UserTemplate.as_view(), name='user'),
    path('edituser', views.EditUser.as_view(), name='edituser'),
    path('deleteuser', views.DeleteUser.as_view(), name='deleteuser'),

    path('<int:user_id>/assignrole/', views.AssignRoleTemplate.as_view(), name='assignrole'),
    path('editassignrole', views.EditAssignRole.as_view(), name='editassignrole'),
    path('deleteassignrole', views.DeleteAssignRole.as_view(), name='deleteassignrole'),

    path('role', views.RoleTemplate.as_view(), name='role'),
    path('editrole', views.EditRole.as_view(), name='editrole'),
    path('deleterole', views.DeleteRole.as_view(), name='deleterole'),

    path('permission', views.PermissionTemplate.as_view(), name='permission'),
    path('editpermission', views.EditPermission.as_view(), name='editpermission'),
    path('deletepermission', views.DeletePermission.as_view(), name='deletepermission'),

    path('<int:role_id>/assignpermission/',views.AssignPermissionTemplate.as_view(), name='assignpermission'),
    path('editassignpermission', views.EditAssignPermission.as_view(), name='editassignpermission'),
    path('deleteassignpermission', views.DeleteAssignPermission.as_view(), name='deleteassignpermission'),
    path('bulkeditassignpermission', views.BulkEditAssignPermission.as_view(), name='bulkeditassignpermission'),
]
