# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.cache import never_cache
from parler.views import ViewUrlMixin
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from rest_framework.settings import api_settings
from shop.views.catalog import AddToCartView as AddToCartViewBase
from shop.views.catalog import ProductListView as BaseProductListView
from shop.views.catalog import ProductRetrieveView

from shopit.conf import app_settings
from shopit.models.cart import Cart, CartItem
from shopit.models.product import Attribute, Product
from shopit.rest.renderers import ModifiedCMSPageRenderer
from shopit.serializers import (AddToCartSerializer, CartItemSerializer, ProductDetailSerializer,
                                ProductSummarySerializer, ReviewSerializer, WatchItemSerializer)

CATEGORIES_VAR = 'c'
BRANDS_VAR = 'b'
MANUFACTURERS_VAR = 'm'
FLAGS_VAR = 'f'
MODIFIERS_VAR = 'd'
PRICE_FROM_VAR = 'pf'
PRICE_TO_VAR = 'pt'
SORT_VAR = 's'


class ProductListView(BaseProductListView):
    serializer_class = ProductSummarySerializer
    renderer_classes = [ModifiedCMSPageRenderer] + api_settings.DEFAULT_RENDERER_CLASSES

    def get(self, request, *args, **kwargs):
        """
        If products are loaded asynchronously, controlled by
        `ASYNC_PRODUCT_LIST` setting, render template without any data.
        """
        if app_settings.ASYNC_PRODUCT_LIST and request.accepted_renderer.format == 'html':
            return Response({})
        return super(ProductListView, self).get(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """
        Return all products count when `count` exists in GET, applicable
        only when format is not html.
        """
        if request.GET.get('get_count', None) and request.accepted_renderer.format != 'html':
            count = self.filter_queryset(self.get_queryset()).count()
            return Response({'count': count})
        return super(ProductListView, self).list(request, *args, **kwargs)

    def get_queryset(self):
        return Product.objects.translated().active().top_level()

    def filter_queryset(self, queryset):
        queryset = super(ProductListView, self).filter_queryset(queryset)

        categories = list(filter(None, self.request.GET.get(CATEGORIES_VAR, '').split(','))) or None
        brands = list(filter(None, self.request.GET.get(BRANDS_VAR, '').split(','))) or None
        manufacturers = list(filter(None, self.request.GET.get(MANUFACTURERS_VAR, '').split(','))) or None
        queryset = queryset.filter_categorization(categories, brands, manufacturers)

        flags = list(filter(None, self.request.GET.get(FLAGS_VAR, '').split(','))) or None
        queryset = queryset.filter_flags(flags)

        modifiers = list(filter(None, self.request.GET.get(MODIFIERS_VAR, '').split(','))) or None
        queryset = queryset.filter_modifiers(modifiers)

        attrs = Attribute.objects.active()
        attr_codes = attrs.values_list('code', flat=True)
        attr_filters = [(x[0], x[1]) for x in self.request.GET.items() if x[0] in attr_codes]

        # Remove null values from attributes that are not nullable.
        for f in [x for x in attr_filters if not x[1]]:
            if not attrs.get(code=f[0]).nullable:
                attr_filters.remove(f)

        queryset = queryset.filter_attributes(attr_filters)

        price_from = self.request.GET.get(PRICE_FROM_VAR, None)
        price_to = self.request.GET.get(PRICE_TO_VAR, None)
        queryset = queryset.filter_price(price_from, price_to)

        sort = self.request.GET.get(SORT_VAR, None)
        if not sort and app_settings.DEFAULT_PRODUCT_ORDER:
            sort = app_settings.DEFAULT_PRODUCT_ORDER
        sort_map = {
            'name': 'translations__name',
            '-name': '-translations__name',
            'price': '_unit_price',
            '-price': '-_unit_price',
        }
        if sort in sort_map:
            queryset = queryset.order_by(sort_map[sort])

        return queryset

    def get_template_names(self):
        return ['shopit/catalog/product_list.html']

    def get_renderer_context(self):
        """
        Add `product_list` renderer context if format is 'html'. Check against
        `ADD_PRODUCT_LIST_TO_CONTEXT` setting if allowed.
        """
        context = super(ProductListView, self).get_renderer_context()
        if app_settings.ADD_PRODUCT_LIST_TO_CONTEXT and context['request'].accepted_renderer.format == 'html':
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
            if page is not None:
                context.update(self.paginator.get_html_context())
            context['product_list'] = page or queryset
        return context


class ProductDetailView(ViewUrlMixin, ProductRetrieveView):
    serializer_class = ProductDetailSerializer
    renderer_classes = [ModifiedCMSPageRenderer] + api_settings.DEFAULT_RENDERER_CLASSES

    def get(self, request, *args, **kwargs):
        response = super(ProductDetailView, self).get(request, *args, **kwargs)
        product_id = self.get_object().pk
        menu = request.toolbar.get_or_create_menu('shopit-menu', _('Shopit'))
        menu.add_break()
        menu.add_modal_item(_('Edit Product'), url=reverse('admin:shopit_product_change', args=[product_id]))
        menu.add_sideframe_item(_('Delete Product'), url=reverse('admin:shopit_product_delete', args=[product_id]))
        return response

    def get_object(self):
        if not hasattr(self, '_product'):
            self._product = get_object_or_404(Product.objects.translated(slug=self.kwargs['slug']))
        return self._product

    def get_template_names(self):
        return ['shopit/catalog/product_detail.html']

    def get_view_url(self):
        """
        Return object view url. Used in `get_translated_url` templatetag from parler.
        """
        return self.get_object().get_absolute_url()


class ProductReviewMixin(object):
    """
    Mixin used in product reviews.
    """
    def get_queryset(self, include_inactive=False):
        return self.get_product().get_reviews(language=self.request.LANGUAGE_CODE, include_inactive=include_inactive)

    def get_product(self):
        if not hasattr(self, '_product'):
            self._product = get_object_or_404(Product.objects.translated(slug=self.kwargs.get('slug')))
        return self._product


class ProductReviewListView(ProductReviewMixin, ListCreateAPIView):
    """
    View that handles listing and creatign reviews on a product.
    """
    serializer_class = ReviewSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES

    @method_decorator(never_cache)
    def get(self, request, *args, **kwargs):
        return super(ProductReviewListView, self).get(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """
        Check that customer is registered, and that the review is not already
        written for this product by the registered customer.
        """
        if not request.customer.is_authenticated():
            errors = {'not-registered': [_('Please register to submit a review.')]}
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        if self.get_queryset(include_inactive=True).filter(customer=request.customer).exists():
            errors = {'exists': [_('Review already written for this Product.')]}
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        data = dict(list(request.data.items()), customer=request.customer, language=request.LANGUAGE_CODE, active=app_settings.REVIEW_ACTIVE_DEFAULT)  # noqa
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(product=self.get_product())
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ProductReviewDetailView(ProductReviewMixin, RetrieveUpdateDestroyAPIView):
    """
    View that handles getting, updating and deleting the review.
    """
    serializer_class = ReviewSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES

    @method_decorator(never_cache)
    def get(self, request, *args, **kwargs):
        return super(ProductReviewDetailView, self).get(request, *args, **kwargs)

    def get_object(self):
        if not hasattr(self, '_object'):
            self._object = get_object_or_404(self.get_queryset(include_inactive=True).filter(id=self.kwargs.get('pk')))
        return self._object

    def update(self, request, *args, **kwargs):
        """
        Only allow update for the review owner.
        """
        if self.get_object().customer != self.request.customer:
            errors = {'not-allowed': [_('You can only update your own reviews.')]}
            return Response(errors, status=status.HTTP_403_FORBIDDEN)
        data = dict(list(request.data.items()), customer=request.customer, language=request.LANGUAGE_CODE)
        serializer = self.get_serializer(self.get_object(), data=data, partial=kwargs.pop('partial', False))
        serializer.is_valid(raise_exception=True)
        serializer.save(product=self.get_product())
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        """
        Only allow delete for the review owner.
        """
        if self.get_object().customer != self.request.customer:
            errors = {'not-allowed': [_('You can only delete your own reviews.')]}
            return Response(errors, status=status.HTTP_403_FORBIDDEN)
        return super(ProductReviewDetailView, self).delete(self.request, *args, **kwargs)


class AddToCartView(AddToCartViewBase):
    """
    View that handles adding product to the cart.
    """
    serializer_class = AddToCartSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES

    def get_context(self, request, **kwargs):
        product = get_object_or_404(Product.objects.translated(slug=self.kwargs['slug']))
        return {'product': product, 'request': request}

    def post(self, request, *args, **kwargs):
        """
        Override to add the product to cart.
        """
        errors = {}
        cart = Cart.objects.get_or_create_from_request(request)
        context = self.get_context(request, **kwargs)
        product = context.pop('product')
        quantity = int(request.data.get('quantity', 1))

        if product.is_group:
            errors['variant'] = [_("You can't add a group product to the cart.")]
        else:
            total_quantity = getattr(product.is_in_cart(cart), 'quantity', 0) + quantity
            available, diff = product.is_available(total_quantity)
            if available:
                item, created = CartItem.objects.get_or_create(
                    cart=cart, product=product, quantity=quantity, product_code=product.product_code)
                serializer_class = WatchItemSerializer if total_quantity == 0 else CartItemSerializer
                serializer = serializer_class(item, context=context)
                return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
            errors['quantity'] = [_('Product not available for given quantity, there is %d left.') % (quantity + diff)]

        return Response(errors, status=status.HTTP_400_BAD_REQUEST)
