# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import itertools
import math

from django import template
from django.db.models import Q
from django.db.models.query import QuerySet
from django.utils import six
from shop.money import Money
from shop.money.money_maker import MoneyMaker

from shopit.forms.shop import CartDiscountCodeForm
from shopit.models import categorization as categorization_models
from shopit.models.cart import Cart
from shopit.models.flag import Flag
from shopit.models.modifier import Modifier
from shopit.models.order import Order
from shopit.models.product import Attribute, Product

register = template.Library()


@register.filter
def moneyformat(value, currency_code=None):
    """
    Format a number into Money type.
    """
    return MoneyMaker(currency_code)(value)


@register.simple_tag(takes_context=True)
def query_transform(context, *args, **kwargs):
    """
    Appends or updates current query string. Can be used as pairs
    passing in every second arg as value so that key can be dynamic.
    It also supports the kwargs format.
    {% query_transform <key> <value> <key> <value> <key>=<value> %}
    """
    get = context['request'].GET.copy()
    if args:
        args_keys = [args[i] for i in range(len(args)) if i % 2 == 0]
        args_vals = [args[i] for i in range(len(args)) if i % 2 != 0]
        for i in range(len(args_vals)):
            k, v = args_keys[i], args_vals[i]
            if v == '' and k in get:
                del get[k]
            elif v != '':
                get[k] = v
    for k, v in kwargs.items():
        if v == '' and k in get:
            del get[k]
        elif v != '':
            get[k] = v
    return get.urlencode()


@register.simple_tag
def get_products(limit=None, flags=None, categories=0, brands=0, manufacturers=0, price_from=None, price_to=None):
    """
    Returns product queryset. Categorization si marked as `0` by default so
    that products with `None` categorizations can be queried. A comma
    separated list of categorization slugs can be passed in.

    {% get_products 3 categories=3 brands='apple' flags='featured,awesome' as featured_products %}
    """
    filters = {}
    products = Product.objects.active()

    if categories != 0:
        if isinstance(categories, six.string_types):
            products = products.filter_categorization(categories=categories.split(','))
        elif isinstance(categories, QuerySet):
            filters['_category_id__in'] = categories.values_list('id', flat=True)
        else:
            filters['_category'] = categories

    if brands != 0:
        if isinstance(brands, six.string_types):
            products = products.filter_categorization(brands=brands.split(','))
        elif isinstance(brands, QuerySet):
            filters['_brand_id__in'] = brands.values_list('id', flat=True)
        else:
            filters['_brand'] = brands

    if manufacturers != 0:
        if isinstance(manufacturers, six.string_types):
            products = products.filter_categorization(manufacturers=manufacturers.split(','))
        elif isinstance(manufacturers, QuerySet):
            filters['_manufacturer_id__in'] = manufacturers.values_list('id', flat=True)
        else:
            filters['_manufacturer'] = manufacturers

    products = products.filter_flags(flags.split(',') if flags else None)
    products = products.filter_price(price_from, price_to)
    return products.top_level().filter(**filters)[:limit]


@register.simple_tag
def get_categorization(categorization, products=None, limit=None, level=None, depth=None, parent=None):
    """
    Returns a categorization list. First argument must be categorization type.
    If `products` is passed in only return categorization appearing in the given list of products.

    {% get_categorization 'brand' products=product_list limit=3 level=1 depth=2 as brands %}
    """
    if categorization not in ['category', 'brand', 'manufacturer']:
        raise template.TemplateSyntaxError(
            "Tag `get_categorization` requires first argument to be either 'category', 'brand' or 'manufacturer'.")

    filters = {}

    if products is not None:
        filters['id__in'] = list(set([getattr(x, '_%s_id' % categorization) for x in products]))

    if level is not None:
        if depth is not None:
            filters['level__gte'] = level
            filters['level__lt'] = level + depth
        else:
            filters['level'] = level

    if parent is not None:
        filters['parent'] = parent

    return getattr(categorization_models, categorization.capitalize()).objects.active().filter(**filters)[:limit]


@register.simple_tag
def get_flags(code=None, products=None, limit=None, level=None, depth=None, parent=None):
    """
    Returns flag with the given code. If code is None returns all, in that
    case products, limit, level, depth & parent can be passed in to filter the results.
    If `products` is passed in only returns flags appearing in the given list of products.

    {% get_flags 'featured' as featured_flag %}
    {% get_flags products=product_list level=1 parent='featured' as featured_flags %}
    """
    if code is not None:
        return Flag.objects.active().filter(code=code).first()

    flags = Flag.objects.active()

    if products is not None:
        flags = flags.filter(Q(product__in=products) | Q(product__group__isnull=False, product__group__in=products))
        flags = flags.distinct()

    filters = {}

    if level is not None:
        if depth is not None:
            filters['level__gte'] = level
            filters['level__lt'] = level + depth
        else:
            filters['level'] = level

    if parent is not None:
        filters['parent'] = parent

    return flags.filter(**filters)[:limit]


@register.simple_tag
def get_modifiers(code=None, products=None, limit=None, filtering=False):
    """
    Return modifier with the given code. If code is None returns all, in that
    case products, limit & filtering can be passed in to filter the results.
    If `products` is passed in only returns modifiers appearing in the given list of products.
    If `filtering` is set to True, only returns modifiers that are eligible for filtering.

    {% get_modifiers 'special-discount' as special_discount_mod %}
    {% get_modifiers products=product_list filtering=True %}
    """
    if code is not None:
        return Modifier.objects.active().filter(code=code).first()

    filters = {}

    if products is not None:
        product_mods = [x.get_modifiers().values_list('code', flat=True) for x in products]
        filters['code__in'] = list(set(itertools.chain.from_iterable(product_mods)))

    modifiers = Modifier.objects.active()

    if filtering:
        modifiers = modifiers.filtering_enabled()

    return modifiers.filter(**filters)[:limit]


@register.simple_tag
def get_attributes(products=None):
    """
    Returns active attributes. If `products` are passed in returns attributes
    only used in the given list of products.

    {% get_attributes products as attributes %}
    """
    attributes = Attribute.objects.active()

    if products is not None:
        product_ids = [x.id for x in products]
        attr_ids = list(set(Product.objects.filter(group_id__in=product_ids).values_list('attributes', flat=True)))
        attributes = attributes.filter(id__in=attr_ids)
    return attributes


@register.simple_tag
def get_price_steps(steps=5, products=None):
    """
    Returns min and max price with the steps in between.

    {% get_price_steps 3 products as price_steps %}
    """
    queryset = Product.objects.active().top_level()

    if products is not None:
        queryset = queryset.filter(id__in=[x.id for x in products])
    if not queryset:
        return []

    queryset = queryset.order_by('_unit_price')
    min_price, max_price = math.floor(queryset.first().unit_price), math.ceil(queryset.last().unit_price)
    if max_price == min_price:
        return [Money(min_price)]

    price_steps = [min_price]
    chunk = int(max_price - min_price) / (steps + 1)
    for i in range(steps):
        price_steps.append(price_steps[-1] + chunk)
    price_steps = sorted(list(set(price_steps)))
    price_steps.append(max_price)
    price_steps = [Money(x) for x in price_steps]
    return price_steps


@register.inclusion_tag('shopit/includes/add_to_cart.html', takes_context=True)
def add_to_cart(context, product=None, watch=False):
    """
    Renders add to cart template. Either the product needs to be available
    within the context, or a product must be passed in. `watch` can be passed
    in to include a watch button as well.

    {% add_to_cart watch=True %}
    """
    product = product or context.get('product', None)
    if not product:
        raise template.TemplateSyntaxError(
            "Tag `add_to_cart` requires to pass in the `product` or for the product to be available in the context.")
    context.update({'product': product, 'watch': watch})
    return context


@register.inclusion_tag('shopit/includes/cart.html', takes_context=True)
def cart(context, editable=True):
    """
    Renders a cart template for the current request. `editable` boolean
    can be passed in to disable cart edits.

    {% cart editable=False %}
    """
    request = context['request']
    cart = context.get('cart') or Cart.objects.get_or_create_from_request(request)
    cart.update(request)

    return {
        'cart': cart,
        'cart_items': cart._cached_cart_items,
        'editable': editable,
        'form': context.get('form', CartDiscountCodeForm(cart=cart)),
    }


@register.inclusion_tag('shopit/includes/order.html', takes_context=True)
def order(context, order=None, number=None):
    """
    Renders order template for the given order or given order number.
    Uses latest order if both `order` and `number` is not passed in.

    {% order number="2018-00001" %}
    """
    if not order and number:
        order_number = Order.resolve_number(number)['number']
        order = Order.objects.filter(number=order_number).first()
    elif not order:
        order = Order.objects.filter_from_request(context['request']).first()

    return {
        'order': order,
        'order_items': order.items.all() if order else [],
    }
