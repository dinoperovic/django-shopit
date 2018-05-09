# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from decimal import Decimal as D

from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore
from django.test import TestCase, override_settings
from django.test.client import RequestFactory
from django.utils.text import slugify
from email_auth.models import User
from shop.money import Money

from shopit.models import categorization as categorization_models
from shopit.models.cart import Cart
from shopit.models.flag import Flag
from shopit.models.modifier import DiscountCode, Modifier, ModifierCondition
from shopit.models.product import (Attachment, Attribute, AttributeChoice, AttributeValue, Customer, Product, Relation,
                                   Review)
from shopit.models.tax import Tax


@override_settings(ROOT_URLCONF='tests.urls')
class ShopitTestCase(TestCase):
    def create_request(self):
        """Create request with user, customer and cart."""
        self.factory = RequestFactory()
        self.request = self.factory.get('/')
        self.user = get_user_model().objects.create(username='user', email='user@example.com', password='resu')
        self.request.user = self.user
        self.request.session = SessionStore()
        self.request.session.create()
        self.customer = Customer.objects.get_from_request(self.request)
        self.customer.recognize_as_registered()
        self.customer.save()
        self.request.customer = self.customer
        self.cart = Cart.objects.get_from_request(self.request)
        self.request.cart = self.cart

    def create_tax(self, name, percent=0, **kwargs):
        attrs = {'name': name, 'percent': D(percent)}
        attrs.update(kwargs)
        return Tax.objects.language().create(**attrs)

    def create_product(self, name, kind=Product.SINGLE, unit_price=0, **kwargs):
        attrs = {'name': name, 'slug': slugify(name), 'code': slugify(name),
                 'kind': kind, 'unit_price': Money(unit_price)}
        attrs.update(kwargs)
        return Product.objects.language().create(**attrs)

    def create_attribute(self, name, choices=[], **kwargs):
        attrs = {'name': name, 'code': slugify(name)}
        attrs.update(kwargs)
        attr = Attribute.objects.language().create(**attrs)
        for choice in choices:
            AttributeChoice.objects.language().create(attribute=attr, value=choice)
        return attr

    def create_attribute_value(self, attribute, product, choice):
        return AttributeValue.objects.create(attribute=attribute, product=product, choice=choice)

    def create_attachment(self, product, kind='image', **kwargs):
        return Attachment.objects.create(product=product, kind=kind, **kwargs)

    def create_relation(self, base, product, **kwargs):
        attrs = {'base': base, 'product': product}
        attrs.update(kwargs)
        return Relation.objects.create(**attrs)

    def create_review(self, product, customer, text='Lorem ipsum dolor sin', rating=5, **kwargs):
        attrs = {'product': product, 'customer': customer, 'text': text, 'rating': rating}
        attrs.update(kwargs)
        return Review.objects.create(**attrs)

    def create_categorization(self, model, name, depth=1, **kwargs):
        model = getattr(categorization_models, model.capitalize(), categorization_models.Category)
        attrs = {'name': name, 'slug': slugify(name)}
        attrs.update(kwargs)
        return model.objects.language().create(**attrs)

    def create_modifier(self, name, amount=0, percent=None, **kwargs):
        attrs = {'name': name, 'code': slugify(name), 'amount': Money(amount),
                 'percent': D(percent) if percent else None}
        attrs.update(kwargs)
        return Modifier.objects.language().create(**attrs)

    def create_modifier_condition(self, modifier, path, value=0, **kwargs):
        attrs = {'modifier': modifier, 'path': path, 'value': value}
        attrs.update(kwargs)
        return ModifierCondition.objects.create(**attrs)

    def create_discount_code(self, modifier, code, **kwargs):
        attrs = {'modifier': modifier, 'code': slugify(code)}
        attrs.update(kwargs)
        return DiscountCode.objects.create(**attrs)

    def create_flag(self, name, **kwargs):
        attrs = {'name': name, 'code': slugify(name)}
        attrs.update(kwargs)
        return Flag.objects.language().create(**attrs)

    def create_customer(self, username, password=None):
        if not password:
            password = User.objects.make_random_password()
        email = '%s@example.com' % username
        attrs = {'username': username, 'email': email, 'password': password}
        user = User.objects.create_user(**attrs)
        customer = Customer.objects.create(user=user)
        customer._password = password
        return customer

    def get_changelist_args(self, modeladmin, **kwargs):
        """
        Returns changelist args for admin ChangeList.
        """
        m = modeladmin
        args = (
            kwargs.pop('list_display', m.list_display),
            kwargs.pop('list_display_links', m.list_display_links),
            kwargs.pop('list_filter', m.list_filter),
            kwargs.pop('date_hierarchy', m.date_hierarchy),
            kwargs.pop('search_fields', m.search_fields),
            kwargs.pop('list_select_related', m.list_select_related),
            kwargs.pop('list_per_page', m.list_per_page),
            kwargs.pop('list_max_show_all', m.list_max_show_all),
            kwargs.pop('list_editable', m.list_editable),
            m,
        )
        assert not kwargs, "Unexpected kwarg %s" % kwargs
        return args
