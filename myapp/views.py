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
            model_column = self._model_columns[col]

            if model_column.has_choices_available:
                search_filters |=\
                    Q(**{col + '__in': model_column.search_in_choices(
                        search_value)})
            else:
                query_param_name = model_column.get_field_search_path()

                search_filters |=\
                    Q(**{query_param_name+'__istartswith': search_value})

        return qs.filter(search_filters)


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
                udata = {'id':u.id, 'email':u.email, 'is_active':u.is_active }
                request.session['user_data'] = udata
                return HttpResponseRedirect('index')
            else:
                return render(request, self.template_name, {'msg': message})
        except Exception:
            print(e)
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
            return JsonResponse({'success': False})


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


class RollDatatableView(DatatablesServerSideView):
	model = Roll
	columns = ['id', 'roll', 'created_on', 'updated_on']
	searchable_columns = ['roll']

	def get_initial_queryset(self):
		qs = super(RollDatatableView, self).get_initial_queryset().order_by('-id')
		return qs


class RollTemplate(generic.TemplateView):
    template_name = 'roll.html'
    model = Roll

    def get_context_data(self, **kwargs):
        context = super(RollTemplate, self).get_context_data(**kwargs)
        context['rolls'] = Roll.objects.all()
        return context

    def post(self, request, *args, **kwargs):
        roll = self.request.POST.get('roll')
        try:
            r = Roll()
            r.roll = roll
            r.save()
            message = "roll added successfully"
            return JsonResponse({'success': True, 'msg':message})
        except ValidationError as e:
            return JsonResponse({'success': False, 'msg':str(e)})


class EditRoll(generic.TemplateView):
    template_name = 'roll.html'
    model = Roll

    def get(self, request, *args, **kwargs):
        roll_id = self.request.GET.get('roll_id')
        rdata = Roll.objects.filter(id=roll_id)
        roll_list = serializers.serialize('json', rdata)
        return JsonResponse(json.loads(roll_list)[0]['fields'])

    def post(self, request, *args, **kwargs):
        roll_id = request.POST.get('roll_id')
        roll = request.POST.get('roll')
        try:
            r = Roll.objects.get(id=roll_id)
            r.roll = roll
            r.save()
            message = "Roll details successfully updated"
            return JsonResponse({'success': True, 'msg':message})
        except ValidationError as e:
            return JsonResponse({'success': False, 'msg':str(e)})


class DeleteRoll(View):
    def get(self, request, *args, **kwargs):
        roll_id = self.request.GET.get('roll_id')
        Roll.objects.filter(id=roll_id).delete()
        return JsonResponse({'success': True})


def read_file(request):
    f = open('myapp/views.py', 'r')
    file_content = f.read()
    f.close()
    return HttpResponse(file_content, content_type="text/plain")

