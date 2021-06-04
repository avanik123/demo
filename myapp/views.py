from django.shortcuts import render
from django.http import JsonResponse, HttpResponseRedirect
from django.views import generic
from django.core import serializers
from django.views.generic.base import View
from django.contrib.auth import *
from django.db import connection
from django.contrib.auth.hashers import make_password
from .models import *
import json


def dictfetchall(cursor):
    "Returns all rows from a cursor as a dict"
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]


class HomeTemplate(generic.TemplateView):
    template_name = 'index.html'
    model = User

    def get(self, request, *args, **kwargs):
        context = {}
        user_login = request.session.get("user_login", False)
        if user_login is True:
            u = request.session["user_data"]
            user = User.objects.get(email=u['email'])
            users = User.objects.count()
            context['users'] = users
            users = Permission.objects.count()
            context['permissions'] = users
            users = Role.objects.count()
            context['roles'] = users
            return render(request, self.template_name, {'user': user, 'context': context})
        else:
            return HttpResponseRedirect('/')


class LoginTemplate(generic.TemplateView):
    template_name = 'login.html'
    model = User

    def get(self, request):
        user_login = request.session.get("user_login", False)
        if user_login is True:
            return HttpResponseRedirect('/dashboard/')
        else:
            return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        email = self.request.POST.get('email')
        password = self.request.POST.get('password')
        try:
            u = User.objects.get(email=email)
            if u.check_password("password") is True:
                request.session['user_login'] = True
                udata = {'id': u.id, 'email': u.email,
                         'password': u.password, 'username': u.username}
                request.session['user_data'] = udata
                print(udata)
                return HttpResponseRedirect('/dashboard/')
            else:
                return render(request, self.template_name, status=401)
        except Exception:
            return render(request, self.template_name, status=401)


def logout(request):
    if request.session["user_login"]:
        del request.session['user_login']
    return HttpResponseRedirect('/')


class UserTemplate(generic.TemplateView):
    template_name = 'user.html'
    model = UserRole

    def get(self, request, *args, **kwargs):
        context = {}
        draw = self.request.GET.get('draw')
        start = self.request.GET.get('start')
        length = self.request.GET.get('length')
        search_value = self.request.GET.get('search[value]')
        order_column = self.request.GET.get('order[0][column]')
        order_dir = self.request.GET.get('order[0][dir]')

        if self.request.is_ajax():
            columns = ['id', 'username', 'email']
            qry = "SELECT * FROM User"
            
            if search_value:
                qry += "  WHERE (id LIKE '%"+search_value+"%' OR "
                qry += "username LIKE '%"+search_value+"%' OR "
                qry += "email LIKE '%"+search_value+"%')"

                # For order
            if order_column and order_dir:
                order_column = int(order_column)
                qry += " ORDER BY " + columns[order_column] + " " + order_dir

            with connection.cursor() as cursor1:
                cursor1.execute(
                    "SELECT count(*) FROM ("+ qry +") as total_count")
                row = cursor1.fetchone()
                permission_count = row[0]
            
            # For limit offset
            if (start is not None) and (length is not None) and length != "-1":
                qry += " LIMIT " + str(start) + "," + str(length)
                
            cursor = connection.cursor()
            cursor.execute(qry)
            permissions = dictfetchall(cursor)
            context['data'] = permissions
            context["draw"] = draw
            context["recordsTotal"] = permission_count 
            context["recordsFiltered"] = permission_count 
            return JsonResponse(context)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        name = self.request.POST.get('name')
        email = self.request.POST.get('email')
        password = self.request.POST.get('password')
        try:
            u = User()
            u.username = name
            u.email = email
            u.password = make_password("password")
            u.save()
            ur = UserRole()
            ur.user_id = u.id
            ur.role_id = 5
            ur.save()
            message = "User added successfully"
            return JsonResponse({'success': True, 'msg': message})
        except Exception as e:
            return JsonResponse({'success': False, 'msg': str(e)})


class EditUser(generic.TemplateView):
    template_name = 'user.html'
    model = User, Role

    def get(self, request, *args, **kwargs):
        user_id = self.request.GET.get('user_id')
        udata = User.objects.filter(id=user_id)
        user_list = serializers.serialize('json', udata)
        # role_list = json.loads(user_list)[0]['fields']['role']
        return JsonResponse(json.loads(user_list)[0]['fields'])

    def post(self, request, *args, **kwargs):
        user_id = request.POST.get('user_id')
        name = request.POST.get('name')
        email = request.POST.get('email')
        # role = request.POST.getlist('role[]')
        # convertList = ','.join(map(str,role))
        try:
            u = User.objects.get(id=user_id)
            u.username = name
            u.email = email
            # u.role = convertList
            u.save()
            message = "User edited successfully"
            return JsonResponse({'success': True, 'msg': message})
        except Exception as e:
            return JsonResponse({'success': False, 'msg': str(e)})


class DeleteUser(View):
    def get(self, request, *args, **kwargs):
        user_id = self.request.GET.get('user_id')
        User.objects.filter(id=user_id).delete()
        return JsonResponse({'success': True})


class AssignRoleTemplate(generic.TemplateView):
    template_name = 'assign_role.html'

    def get(self, request, user_id, *args, **kwargs):
        context = {}
        userdata = User.objects.filter(id=user_id)
        user_list = serializers.serialize('json', userdata)
        user_id = json.loads(user_list)[0]['pk']
        context['users'] = user_id
        user_name = json.loads(user_list)[0]['fields']['username']
        context['username'] = user_name

        draw = self.request.GET.get('draw')
        start = self.request.GET.get('start')
        length = self.request.GET.get('length')
        search_value = self.request.GET.get('search[value]')
        order_column = self.request.GET.get('order[0][column]')
        order_dir = self.request.GET.get('order[0][dir]')

        if self.request.is_ajax():
            columns = ['all_role_id', 'role_id', 'role', 'create_date', 'update_date']
            qry = " SELECT UR.role_id, R.id as all_role_id, R.role, R.created_on as create_date, R.updated_on as update_date FROM Role as R LEFT JOIN UserRole as UR ON UR.role_id=R.id AND UR.user_id = "+str(user_id)+" "
            
            # For search
            if search_value:
                qry += "  WHERE (all_role_id LIKE '%"+search_value+"%' OR "     
                qry += "R.role LIKE '%"+search_value+"%' OR "
                qry += "R.created_on LIKE '%"+search_value+"%' OR "           
                qry += "R.updated_on LIKE '%"+search_value+"%')"

            # For order
            if order_column and order_dir:
                order_column = int(order_column)
                qry += " ORDER BY " + columns[order_column] + " " + order_dir

            with connection.cursor() as cursor1:
                cursor1.execute(
                    "SELECT count(*) FROM ("+ qry +") as total_count")
                row = cursor1.fetchone()
                permission_count = row[0]
            
            # For limit offset
            if (start is not None) and (length is not None) and length != "-1":
                qry += " LIMIT " + str(start) + "," + str(length)
                
            cursor = connection.cursor()
            cursor.execute(qry)
            permissions = dictfetchall(cursor)
            context['data'] = permissions
            context["draw"] = draw
            context["recordsTotal"] = permission_count 
            context["recordsFiltered"] = permission_count 
            return JsonResponse(context)
        return render(request, self.template_name, context)


class EditAssignRole(generic.TemplateView):
    template_name = 'assign_role.html'
    model = User, Role

    def get(self, request, *args, **kwargs,):
        role_id = self.request.GET.get('role_id')
        user_id = self.request.GET.get('user_id')
        udata = User.objects.filter(id=user_id)
        user_list = serializers.serialize('json', udata)
        return JsonResponse(json.loads(user_list)[0]['fields'])

    def post(self, request, *args, **kwargs):
        role_id = self.request.POST.get('role_id')
        user_id = self.request.POST.get('user_id')
        try:
            ur = UserRole()
            ur.role_id = role_id
            ur.user_id = user_id
            ur.save()
            message = "Role details successfully updated"
            return JsonResponse({'success': True, 'msg': message})
        except Exception as e:
            return JsonResponse({'success': False, 'msg': str(e)})


class DeleteAssignRole(View):
    def get(self, request, *args, **kwargs):
        role_id = self.request.GET.get('role_id')
        UserRole.objects.filter(role_id=role_id).delete()
        return JsonResponse({'success': True})


class RoleTemplate(generic.TemplateView):
    template_name = 'role.html'

    def get(self, request, *args, **kwargs):
        context = {}
        draw = self.request.GET.get('draw')
        start = self.request.GET.get('start')
        length = self.request.GET.get('length')
        search_value = self.request.GET.get('search[value]')
        order_column = self.request.GET.get('order[0][column]')
        order_dir = self.request.GET.get('order[0][dir]')

        if self.request.is_ajax():
            columns = ['id', 'role', 'created_on', 'updated_on']
            qry = "SELECT * FROM Role"
            
            if search_value:
                qry += "  WHERE (id LIKE '%"+search_value+"%' OR "
                qry += "role LIKE '%"+search_value+"%' OR "
                qry += "created_on LIKE '%"+search_value+"%' OR "
                qry += "updated_on LIKE '%"+search_value+"%')"

                # For order
            if order_column and order_dir:
                order_column = int(order_column)
                qry += " ORDER BY " + columns[order_column] + " " + order_dir

            with connection.cursor() as cursor1:
                cursor1.execute(
                    "SELECT count(*) FROM ("+ qry +") as total_count")
                row = cursor1.fetchone()
                permission_count = row[0]
            
            # For limit offset
            if (start is not None) and (length is not None) and length != "-1":
                qry += " LIMIT " + str(start) + "," + str(length)
                
            cursor = connection.cursor()
            cursor.execute(qry)
            permissions = dictfetchall(cursor)
            context['data'] = permissions
            context["draw"] = draw
            context["recordsTotal"] = permission_count 
            context["recordsFiltered"] = permission_count 
            return JsonResponse(context)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        role = self.request.POST.get('role')
        # permission = self.request.POST.getlist('permission[]')
        # convertList = ','.join(map(str, permission))
        try:
            r = Role()
            r.role = role
            r.save()
            message = "roll added successfully"
            return JsonResponse({'success': True, 'msg': message})
        except Exception as e:
            return JsonResponse({'success': False, 'msg': str(e)})


class EditRole(generic.TemplateView):
    template_name = 'role.html'
    model = Role

    def get(self, request, *args, **kwargs):
        role_id = self.request.GET.get('role_id')
        rdata = Role.objects.filter(id=role_id)
        role_list = serializers.serialize('json', rdata)
        return JsonResponse(json.loads(role_list)[0]['fields'])

    def post(self, request, *args, **kwargs):
        role_id = request.POST.get('role_id')
        role = request.POST.get('role')
        permission = request.POST.getlist('permission[]')
        convertList = ','.join(map(str, permission))
        try:
            r = Role.objects.get(id=role_id)
            r.role = role
            r.permission = convertList
            r.save()
            message = "Roll details successfully updated"
            return JsonResponse({'success': True, 'msg': message})
        except Exception as e:
            return JsonResponse({'success': False, 'msg': str(e)})


class DeleteRole(View):
    def get(self, request, *args, **kwargs):
        role_id = self.request.GET.get('role_id')
        Role.objects.filter(id=role_id).delete()
        return JsonResponse({'success': True})


class PermissionTemplate(generic.TemplateView):
    template_name = 'permission.html'
    model = Permission

    def get(self, request, *args, **kwargs):
        context = {}
        draw =  self.request.GET.get('draw')
        start = self.request.GET.get('start')
        length = self.request.GET.get('length')
        search_value = self.request.GET.get('search[value]')
        order_column = self.request.GET.get('order[0][column]')
        order_dir = self.request.GET.get('order[0][dir]')

        if self.request.is_ajax():
            columns = ['id', 'permission', 'method', 'created_on', 'updated_on']
            qry = "SELECT * FROM Permission"
            
            # For search
            if search_value:
                qry += "  WHERE (id LIKE '%"+search_value+"%' OR "
                qry += "permission LIKE '%"+search_value+"%' OR "
                qry += "method LIKE '%"+search_value+"%' OR "
                qry += "created_on LIKE '%"+search_value+"%' OR "
                qry += "updated_on LIKE '%"+search_value+"%')"

            # For order
            if order_column and order_dir:
                order_column = int(order_column)
                qry += " ORDER BY " + columns[order_column] + " " + order_dir

            with connection.cursor() as cursor1:
                cursor1.execute(
                    "SELECT count(*) FROM ("+ qry +") as total_count")
                row = cursor1.fetchone()
                permission_count = row[0]
            
            # For limit offset
            if (start is not None) and (length is not None) and length != "-1":
                qry += " LIMIT " + str(start) + "," + str(length)
                
            cursor = connection.cursor()
            cursor.execute(qry)
            permissions = dictfetchall(cursor)
            context['data'] = permissions
            context["draw"] = draw
            context["recordsTotal"] = permission_count 
            context["recordsFiltered"] = permission_count 
            return JsonResponse(context)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        # import pdb; pdb.set_trace()
        permission = self.request.POST.get('permission')
        method = self.request.POST.get('method')
        try:
            Permission.objects.get(permission=permission, method= method) 
        except Permission.DoesNotExist:
            p = Permission()
            p.permission = permission
            p.method = method
            p.save()
            return JsonResponse({'success': False, 'msg': "permission added successfully"}, status=200)
        except Permission.MultipleObjectsReturned:
            return JsonResponse({'success': False, 'msg': "Method is already exists."}, status=422)
        except Exception as e:
            return JsonResponse({'success': False, 'msg': str(e)})
        return JsonResponse({'success': True, 'msg': "Something went wrong!"}, status=400)


class EditPermission(generic.TemplateView):
    template_name = 'permission.html'
    model = Permission

    def get(self, request, *args, **kwargs):
        permission_id = self.request.GET.get('permission_id')
        pdata = Permission.objects.filter(id=permission_id)
        permission_list = serializers.serialize('json', pdata)
        return JsonResponse(json.loads(permission_list)[0]['fields'])

    def post(self, request, *args, **kwargs):
        permission_id = request.POST.get('permission_id')
        permission = request.POST.get('permission')
        method = request.POST.get('method')
        try:
            p = Permission.objects.get(id=permission_id)
            p.permission = permission
            p.method = method
            p.save()
            message = "Permission details successfully updated"
            return JsonResponse({'success': True, 'msg': message})
        except Exception as e:
            return JsonResponse({'success': False, 'msg': str(e)})


class DeletePermission(View):
    def get(self, request, *args, **kwargs):
        permission_id = self.request.GET.get('permission_id')
        Permission.objects.filter(id=permission_id).delete()
        return JsonResponse({'success': True})


class BulkDeletePermission(View):
    def get(self, request, *args, **kwargs):
        permission_id = self.request.GET.getlist('permission_id[]')
        Permission.objects.filter(id__in=permission_id).delete()
        return JsonResponse({'success': True})


class AssignPermissionTemplate(generic.TemplateView):
    template_name = 'assign_permission.html'

    def get(self, request, role_id, *args, **kwargs):
        context = {}
        roledata = Role.objects.filter(id=role_id)
        role_list = serializers.serialize('json', roledata)
        role_id = json.loads(role_list)[0]['pk']
        context['roles'] = role_id
        role_name = json.loads(role_list)[0]['fields']['role']
        context['rolename'] = role_name
        
        draw = self.request.GET.get('draw')
        start = self.request.GET.get('start')
        length = self.request.GET.get('length')
        search_value = self.request.GET.get('search[value]')
        order_column = self.request.GET.get('order[0][column]')
        order_dir = self.request.GET.get('order[0][dir]')

        if self.request.is_ajax():
            columns = ['all_permission_id', 'all_permission_id', 'permission_id', 'permission', 'method', 'create_date', 'update_date']
            qry = " SELECT RP.permission_id, P.id as all_permission_id, P.permission, P.method, P.created_on as create_date, P.updated_on as update_date FROM Permission as P LEFT JOIN RolePermission as RP ON RP.permission_id=P.id AND RP.role_id = "+str(role_id)+" "
            
            # For search
            if search_value:
                qry += "  WHERE (all_permission_id LIKE '%"+search_value+"%' OR "
                qry += "P.permission LIKE '%"+search_value+"%' OR "
                qry += "P.method LIKE '%"+search_value+"%' OR "
                qry += "P.created_on LIKE '%"+search_value+"%' OR "
                qry += "P.updated_on LIKE '%"+search_value+"%')"

            # For order
            if order_column and order_dir:
                order_column = int(order_column)
                print(order_column, order_dir)
                qry += " ORDER BY " + columns[order_column] + " " + order_dir

            with connection.cursor() as cursor1:
                cursor1.execute(
                    "SELECT count(*) FROM ("+ qry +") as total_count")
                row = cursor1.fetchone()
                permission_count = row[0]
            
            # For limit offset
            if (start is not None) and (length is not None) and length != "-1":
                qry += " LIMIT " + str(start) + "," + str(length)
                
            cursor = connection.cursor()
            cursor.execute(qry)
            permissions = dictfetchall(cursor)
            context['data'] = permissions
            context["draw"] = draw
            context["recordsTotal"] = permission_count 
            context["recordsFiltered"] = permission_count 
            return JsonResponse(context)
        return render(request, self.template_name, context)


class EditAssignPermission(generic.TemplateView):
    template_name = 'assign_permission.html'

    def post(self, request, *args, **kwargs):
        role_id = self.request.POST.get('role_id')
        permission_id = self.request.POST.get('permission_id')
        try:
            rp = RolePermission()
            rp.role_id = role_id
            rp.permission_id = permission_id
            rp.save()
            message = "Permission details successfully updated"
            return JsonResponse({'success': True, 'msg': message})
        except Exception as e:
            return JsonResponse({'success': False, 'msg': str(e)})


class DeleteAssignPermission(View):
    def get(self, request, *args, **kwargs):
        permission_id = self.request.GET.get('permission_id')
        RolePermission.objects.filter(permission_id=permission_id).delete()
        return JsonResponse({'success': True})


class BulkEditAssignPermission(generic.TemplateView):
    template_name = 'assign_permission.html'

    def post(self, request, *args, **kwargs):
        role_id = self.request.POST.get('role_id')
        permission_id = self.request.POST.getlist('permission_id[]')
        try:
            for i in permission_id:
                RolePermission.objects.get(role_id = role_id, permission_id = i) 
        except RolePermission.DoesNotExist:
            for i in permission_id:
                rp = RolePermission()
                rp.role_id = role_id
                rp.permission_id = i
                rp.save()
            return JsonResponse({'success': False, 'msg': "rolepermission added successfully"}, status=200)
        except RolePermission.MultipleObjectsReturned:
            return JsonResponse({'success': False, 'msg': "Permission is already exists."}, status=422)
        except Exception as e:
            return JsonResponse({'success': False, 'msg': str(e)})
        return JsonResponse({'success': True, 'msg': "Something went wrong!"}, status=400)
        