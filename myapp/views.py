from django.shortcuts import render
from django.views.generic import TemplateView
from myapp import models
from myapp import serializers
from rest_framework import generics
from rest_framework import status
from django.contrib import messages
from rest_framework.response import Response
from django.core.serializers import serialize


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


class ProductDatatableView(DatatablesServerSideView):
	model = models.Product
	columns = ['pro_name']
	searchable_columns = ['pro_name']
    # orderable_columns = []

	def get_initial_queryset(self):
		qs = super(ProductDatatableView, self).get_initial_queryset()
		return qs


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


