# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from parler.views import ViewUrlMixin
from rest_framework.generics import ListAPIView
from rest_framework.settings import api_settings
from shop.rest.renderers import CMSPageRenderer

from shopit.models.categorization import Brand, Category, Manufacturer
from shopit.serializers import BrandSerializer, CategorySerializer, ManufacturerSerializer
from shopit.views.product import ProductListView


class CategorizationViewMixin(object):
    """
    Categorization mixin that makes sure `categorization_model` is specified
    and generates `categorization_model_name`.
    """
    categorization_model = None
    categorization_model_name = None

    def __init__(self, *args, **kwargs):
        super(CategorizationViewMixin, self).__init__(*args, **kwargs)
        if self.categorization_model is None:
            raise ImproperlyConfigured('Must specify `categorization_model` attribute.')

        if self.categorization_model_name is None:
            self.categorization_model_name = self.categorization_model._meta.model.__name__.lower()


class CategorizationListViewBase(CategorizationViewMixin, ListAPIView):
    """
    Base categorization list view.
    """
    serializers_class = None
    renderer_classes = [CMSPageRenderer] + api_settings.DEFAULT_RENDERER_CLASSES
    template_name = 'shopit/catalog/categorization_list.html'

    def get_queryset(self):
        return self.categorization_model.objects.active()

    def get_template_names(self):
        return ['shopit/catalog/%s_list.html' % self.categorization_model_name, self.template_name]

    def get_renderer_context(self):
        context = super(CategorizationListViewBase, self).get_renderer_context()
        if context['request'].accepted_renderer.format == 'html':
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
            if page is not None:
                context.update(self.paginator.get_html_context())
            context['categorization_list'] = context['%s_list' % self.categorization_model_name] = page or queryset
        return context


class CategoryListView(CategorizationListViewBase):
    categorization_model = Category
    serializer_class = CategorySerializer


class BrandListView(CategorizationListViewBase):
    categorization_model = Brand
    serializer_class = BrandSerializer


class ManufacturerListView(CategorizationListViewBase):
    categorization_model = Manufacturer
    serializer_class = ManufacturerSerializer


class CategorizationDetailViewBase(CategorizationViewMixin, ViewUrlMixin, ProductListView):
    """
    Base categorization detail view.
    A ProductListView with filtered products by current categorization layer.
    """
    template_name = 'shopit/catalog/categorization_detail.html'

    def get(self, request, *args, **kwargs):
        response = super(CategorizationDetailViewBase, self).get(request, *args, **kwargs)
        categorization_id = self.get_categorization_object().pk
        name = self.categorization_model_name
        change_url = reverse('admin:shopit_%s_change' % name, args=[categorization_id])
        delete_url = reverse('admin:shopit_%s_delete' % name, args=[categorization_id])
        menu = request.toolbar.get_or_create_menu('shopit-menu', _('Shopit'))
        menu.add_break()
        menu.add_modal_item(_('Edit %s') % name.capitalize(), url=change_url)
        menu.add_sideframe_item(_('Delete %s') % name.capitalize(), url=delete_url)
        return response

    def get_queryset(self):
        queryset = super(CategorizationDetailViewBase, self).get_queryset()
        categorization = self.get_categorization_object()
        ids = categorization.get_descendants(include_self=True).values_list('pk', flat=True)
        return queryset.filter(**{'_%s_id__in' % self.categorization_model_name: ids})

    def get_template_names(self):
        return ['shopit/catalog/%s_detail.html' % self.categorization_model_name, self.template_name]

    def get_renderer_context(self):
        context = super(CategorizationDetailViewBase, self).get_renderer_context()
        context['categorization'] = context[self.categorization_model_name] = self.get_categorization_object()
        return context

    def get_categorization_object(self):
        if not hasattr(self, '_categorization_object'):
            path = self.kwargs['path']
            slug = path.split('/').pop()
            queryset = self.categorization_model.objects.translated(slug=slug)
            categorization = get_object_or_404(queryset)
            if categorization.get_path() != path:
                raise Http404
            setattr(self, '_categorization_object', categorization)
        return getattr(self, '_categorization_object')

    def get_view_url(self):
        """
        Return object view url. Used in `get_translated_url` templatetag from parler.
        """
        return self.get_categorization_object().get_absolute_url()


class CategoryDetailView(CategorizationDetailViewBase):
    categorization_model = Category


class BrandDetailView(CategorizationDetailViewBase):
    categorization_model = Brand


class ManufacturerDetailView(CategorizationDetailViewBase):
    categorization_model = Manufacturer
