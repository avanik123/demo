from django.shortcuts import render
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.views.generic import TemplateView
from django.views import generic
from django.contrib import messages
from django.core import serializers
import json
from django.views.generic.base import View
from .models import *
from django.contrib.auth import *
from django.contrib.auth.hashers import make_password
from django.db import connection

from django.core.paginator import Paginator
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q
from django.http.response import HttpResponse, HttpResponseBadRequest
from django.views.generic import View
from myapp.parameters import (
    Column, ForeignColumn,
    ColumnLink, PlaceholderColumnLink,
    Order, ColumnOrderError)
import json

DATATABLES_SERVERSIDE_MAX_COLUMNS = 30

class DatatablesServerSideView(View):
    columns = []
    searchable_columns = []
    foreign_fields = {}
    model = None

    def __init__(self, *args, **kwargs):
        super(DatatablesServerSideView, self).__init__(*args, **kwargs)
        fields = {f.name: f for f in self.model._meta.get_fields()}

        model_columns = {}
        for col_name in self.columns:
            if col_name in self.foreign_fields:
                new_column = ForeignColumn(
                    col_name, self.model,
                    self.foreign_fields[col_name])
            else:
                new_column = Column(fields[col_name])

            model_columns[col_name] = new_column

        self._model_columns = model_columns
        self.foreign_fields = self.foreign_fields

    def get(self, request, *args, **kwargs):
        if not request.is_ajax():
            return HttpResponseBadRequest()
        try:
            params = self.read_parameters(request.GET)
        except ValueError:
            return HttpResponseBadRequest()

        # Prepare the queryset and apply the search and order filters
        qs = self.get_initial_queryset()

        if 'search_value' in params:
            qs = self.filter_queryset(params['search_value'], qs)

        if len(params['orders']):
            qs = qs.order_by(
                *[order.get_order_mode() for order in params['orders']])

        paginator = Paginator(qs, params['length'])
        return HttpResponse(
            json.dumps(
                self.get_response_dict(paginator, params['draw'],
                                       params['start']),
                cls=DjangoJSONEncoder
            ),
            content_type="application/json")

    def read_parameters(self, query_dict):
        """ Converts and cleans up the GET parameters. """
        params = {field: int(query_dict[field]) for field
                  in ['draw', 'start', 'length']}

        column_index = 0
        has_finished = False
        column_links = []

        while column_index < DATATABLES_SERVERSIDE_MAX_COLUMNS and\
                not has_finished:
            column_base = 'columns[%d]' % column_index

            try:
                column_name = query_dict[column_base + '[name]']
                if column_name != '':
                    column_links.append(ColumnLink(
                        column_name,
                        self._model_columns[column_name],
                        query_dict.get(column_base + '[orderable]'),
                        query_dict.get(column_base + '[searchable]')))
                else:
                    column_links.append(PlaceholderColumnLink())
            except KeyError:
                has_finished = True

            column_index += 1

        orders = []
        order_index = 0
        has_finished = False
        while order_index < len(self.columns) and not has_finished:
            try:
                order_base = 'order[%d]' % order_index
                order_column = query_dict[order_base + '[column]']
                orders.append(Order(
                    order_column,
                    query_dict[order_base + '[dir]'],
                    column_links))
            except ColumnOrderError:
                pass
            except KeyError:
                has_finished = True

            order_index += 1

        search_value = query_dict.get('search[value]')
        if search_value:
            params['search_value'] = search_value

        params.update({'column_links': column_links, 'orders': orders})
        return params

    def get_initial_queryset(self):
        return self.model.objects.all()

    def render_column(self, row, column):
        return self._model_columns[column].render_column(row)

    def prepare_results(self, qs):
        json_data = []

        for cur_object in qs:
            retdict = {fieldname: self.render_column(cur_object, fieldname)
                       for fieldname in self.columns}
            self.customize_row(retdict, cur_object)
            json_data.append(retdict)
        return json_data

    def get_response_dict(self, paginator, draw_idx, start_pos):
        page_id = (start_pos // paginator.per_page) + 1
        if page_id > paginator.num_pages:
            page_id = paginator.num_pages
        elif page_id < 1:
            page_id = 1

        objects = self.prepare_results(paginator.page(page_id))
        return {"draw": draw_idx,
                "recordsTotal": paginator.count,
                "recordsFiltered": paginator.count,
                "data": objects}

    def customize_row(self, row, obj):
        pass

    def choice_field_search(self, column, search_value):
        values_dict = self.choice_fields_completion[column]
        matching_choices = [val for key, val in six.iteritems(values_dict)
                            if key.startswith(search_value)]
        return Q(**{column + '__in': matching_choices})

    def filter_queryset(self, search_value, qs):
        search_filters = Q()
        for col in self.searchable_columns:
            print("=====", col)
            model_column = self._model_columns[col]
            print("++++", model_column)

            if model_column.has_choices_available:
                search_filters |=\
                    Q(**{col + '__in': model_column.search_in_choices(
                        search_value)})
            else:
                query_param_name = model_column.get_field_search_path()

                search_filters |=\
                    Q(**{query_param_name+'__istartswith': search_value})

        return qs.filter(search_filters)


def dictfetchall(cursor):
    "Returns all rows from a cursor as a dict"
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]

    
class LoginTemplate(generic.TemplateView):
    template_name = 'login.html'
    model = User

    def post(self, request, *args, **kwargs):
        email = self.request.POST.get('email')
        password = self.request.POST.get('password')
        try:
            u = User.objects.get(email=email)
            message = "Invalid password"
            if u.check_password(password) is True:
                request.session['user_login'] = True
                udata = {'id':u.id, 'email':u.email, 'password':u.password }
                request.session['user_data'] = udata
                return HttpResponseRedirect('/index/')
            else:
                return render(request, self.template_name, {'msg': message})
        except Exception as e:
            message = "Invalid email"
            return render(request, self.template_name, {'msg': message})


class HomeTemplate(generic.TemplateView):
    template_name = 'index.html'
    model = User
    
    def get(self, request):
        user_login = request.session.get("user_login", False)
        if user_login is True:
            u = request.session["user_data"]
            user = User.objects.get(email=u['email'])
            return render(request, self.template_name, {'user': user})
        else:
            return HttpResponseRedirect('/')


class UserDatatableView(DatatablesServerSideView):
	model = User
	columns = ['id', 'username', 'email']
	searchable_columns = ['username']
    # orderable = ['id']

	def get_initial_queryset(self):
		qs = super(UserDatatableView, self).get_initial_queryset().order_by('-id')
		return qs


class UserTemplate(generic.TemplateView):
    template_name = 'user.html'
    model = User, Role

    def get_context_data(self, **kwargs):
        context = super(UserTemplate, self).get_context_data(**kwargs)
        context['users'] = User.objects.all()
        # context['roles'] = Role.objects.all()
        return context

    def post(self, request, *args, **kwargs):
        name = self.request.POST.get('name')
        email = self.request.POST.get('email')
        # role = self.request.POST.getlist('role[]')
        # convertList = ','.join(map(str,role))
        password = self.request.POST.get('password')
        try:
            u = User()
            u.username = name
            u.email = email
            # u.role = convertList
            u.password = make_password(password = password)
            u.save()
            message = "User added successfully"
            return JsonResponse({'success': True, 'msg':message})
        except Exception as e:
            return JsonResponse({'success': False, 'msg':str(e)})


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
            return JsonResponse({'success': True, 'msg':message})
        except Exception as e:
            return JsonResponse({'success': False, 'msg':str(e)})


class DeleteUser(View):
    def get(self, request, *args, **kwargs):
        user_id = self.request.GET.get('user_id')
        User.objects.filter(id=user_id).delete()
        return JsonResponse({'success': True})


class AssignRoleDatatableView(DatatablesServerSideView):
	model = Role
	columns = ['id', 'role', 'created_on', 'updated_on']
	searchable_columns = ['role']

	def get_initial_queryset(self):
		qs = super(AssignRoleDatatableView, self).get_initial_queryset().order_by('-id')
		return qs


class AssignRoleTemplate(generic.TemplateView):
    template_name = 'assign_role.html'
    model = User, Role, UserRole

    def get_context_data(self, user_id, **kwargs):
        context = super(AssignRoleTemplate, self).get_context_data(**kwargs)
        context['users'] = User.objects.all()
        context['roles'] = Role.objects.all()
        udata = User.objects.filter(id=user_id)
        user_list = serializers.serialize('json', udata)
        user_id = json.loads(user_list)[0]['pk']
        context['user_id'] = user_id
        return context


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
            ur.role_id_id = role_id
            ur.user_id_id = user_id
            ur.save()
            message = "Role details successfully updated"
            return JsonResponse({'success': True, 'msg':message})
        except Exception as e:
            return JsonResponse({'success': False, 'msg':str(e)})


class ProductDatatableView(DatatablesServerSideView):
	model = Product
	columns = ['id', 'pro_name', 'created_on', 'updated_on']
	searchable_columns = ['pro_name']

	def get_initial_queryset(self):
		qs = super(ProductDatatableView, self).get_initial_queryset().order_by('-id')
		return qs


class ProductTemplate(generic.TemplateView):
    template_name = 'product.html'
    model = Product

    def get_context_data(self, **kwargs):
        context = super(ProductTemplate, self).get_context_data(**kwargs)
        context['products'] = Product.objects.all()
        return context

    def post(self, request, *args, **kwargs):
        pname = self.request.POST.get('pname')
        try:
            p = Product()
            p.pro_name = pname
            p.save()
            message = "Product added successfully"
            return JsonResponse({'success': True, 'msg':message})
        except Exception as e:
            return JsonResponse({'success': False, 'msg':str(e)})


class EditProduct(generic.TemplateView):
    template_name = 'product.html'
    model = Product

    def get(self, request, *args, **kwargs):
        product_id = self.request.GET.get('product_id')
        pdata = Product.objects.filter(id=product_id)
        product_list = serializers.serialize('json', pdata)
        return JsonResponse(json.loads(product_list)[0]['fields'])

    def post(self, request, *args, **kwargs):
        product_id = request.POST.get('product_id')
        pname = request.POST.get('pname')
        try:
            p = Product.objects.get(id=product_id)
            p.pro_name = pname
            p.save()
            message = "Product details successfully updated"
            return JsonResponse({'success': True, 'msg':message})
        except ValidationError as e:
            return JsonResponse({'success': False, 'msg':str(e)})


class DeleteProduct(View):
    def get(self, request, *args, **kwargs):
        product_id = self.request.GET.get('product_id')
        Product.objects.filter(id=product_id).delete()
        return JsonResponse({'success': True})


class RoleDatatableView(DatatablesServerSideView):
	model = Role
	columns = ['id', 'role', 'created_on', 'updated_on']
	searchable_columns = ['role']

	def get_initial_queryset(self):
		qs = super(RoleDatatableView, self).get_initial_queryset().order_by('-id')
		return qs


class RoleTemplate(generic.TemplateView):
    template_name = 'role.html'
    model = Role, Permission

    def get_context_data(self, **kwargs):
        context = super(RoleTemplate, self).get_context_data(**kwargs)
        context['roles'] = Role.objects.all()
        context['permissions'] = Permission.objects.all()
        return context

    def post(self, request, *args, **kwargs):
        role = self.request.POST.get('role')
        permission = self.request.POST.getlist('permission[]')
        convertList = ','.join(map(str,permission))
        try:
            r = Role.object.create_in_bulk()
            r.role = role
            r.permission = convertList
            r.save()
            message = "roll added successfully"
            return JsonResponse({'success': True, 'msg':message})
        except Exception as e:
            return JsonResponse({'success': False, 'msg':str(e)})


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
        convertList = ','.join(map(str,permission))
        try:
            r = Role.objects.get(id=role_id)
            r.role = role
            r.permission = convertList
            r.save()
            message = "Roll details successfully updated"
            return JsonResponse({'success': True, 'msg':message})
        except Exception as e:
            return JsonResponse({'success': False, 'msg':str(e)})


class DeleteRole(View):
    def get(self, request, *args, **kwargs):
        role_id = self.request.GET.get('role_id')
        Role.objects.filter(id=role_id).delete()
        return JsonResponse({'success': True})


class PermissionDatatableView(DatatablesServerSideView):
	model = Permission
	columns = ['id', 'permission', 'method', 'created_on', 'updated_on']
	searchable_columns = ['permission']

	def get_initial_queryset(self):
		qs = super(PermissionDatatableView, self).get_initial_queryset().order_by('-id')
		return qs


class PermissionTemplate(generic.TemplateView):
    template_name = 'permission.html'
    model = Permission

    def get_context_data(self, **kwargs):
        context = super(PermissionTemplate, self).get_context_data(**kwargs)
        context['permissions'] = Permission.objects.all()
        return context

    def post(self, request, *args, **kwargs):
        permission = self.request.POST.get('permission')
        method = self.request.POST.get('method')
        try:
            p = Permission()
            p.permission = permission
            p.method = method
            p.save()
            message = "permission added successfully"
            return JsonResponse({'success': True, 'msg':message})
        except Exception as e:
            return JsonResponse({'success': False, 'msg':str(e)})


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
            return JsonResponse({'success': True, 'msg':message})
        except Exception as e:
            return JsonResponse({'success': False, 'msg':str(e)})


class DeletePermission(View):
    def get(self, request, *args, **kwargs):
        permission_id = self.request.GET.get('permission_id')
        Permission.objects.filter(id=permission_id).delete()
        return JsonResponse({'success': True})


class AssignPermissionDatatableView(DatatablesServerSideView):
	model = Permission
	columns = ['id', 'permission', 'method', 'created_on', 'updated_on']
	searchable_columns = ['permission']

	def get_initial_queryset(self):
		qs = super(AssignPermissionDatatableView, self).get_initial_queryset().order_by('-id')
		return qs


class AssignPermissionTemplate(generic.TemplateView):
    template_name = 'assign_permission.html'
    model = Permission, Role, RolePermission

    def get_context_data(self, role_id, **kwargs):
        context = super(AssignPermissionTemplate, self).get_context_data(**kwargs)
        context['roles'] = Role.objects.all()
        qry = "SELECT myapp_RolePermission.permission_id_id FROM myapp_RolePermission LEFT JOIN myapp_Permission ON myapp_RolePermission.id=myapp_Permission.id"
        cursor = connection.cursor()
        cursor.execute(qry)
        datas = dictfetchall(cursor)
        print(type(datas))
        context['rolepermission'] = datas

        pdata = Role.objects.filter(id=role_id)
        permission_list = serializers.serialize('json', pdata)
        role_id = json.loads(permission_list)[0]['pk']
        context['role_id'] = role_id
        return context


class EditAssignPermission(generic.TemplateView):
    template_name = 'assign_permission.html'
    model = Permission, Role

    def get(self, request, *args, **kwargs,):
        role_id = self.request.GET.get('role_id')
        permission_id = self.request.GET.get('permission_id')
        pdata = Permission.objects.filter(id=permission_id)
        permission_list = serializers.serialize('json', pdata)
        return JsonResponse(json.loads(permission_list)[0]['fields'])

    def post(self, request, *args, **kwargs):
        role_id = self.request.POST.get('role_id')
        permission_id = self.request.POST.get('permission_id')
        try:
            rp = RolePermission()
            rp.role_id_id = role_id
            rp.permission_id_id = permission_id
            rp.save()
            message = "Permission details successfully updated"
            return JsonResponse({'success': True, 'msg':message})
        except Exception as e:
            return JsonResponse({'success': False, 'msg':str(e)})