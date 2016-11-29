# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from decimal import Decimal as D

from django.test import TestCase
from django.utils.text import slugify
from shop.money import Money

from shopit.models import categorization as categorization_models
from shopit.models.flag import Flag
from shopit.models.modifier import Modifier
from shopit.models.product import Attachment, Attribute, AttributeChoice, AttributeValue, Product, Relation, Review
from shopit.models.tax import Tax


class ShopitTestCase(TestCase):
    def create_tax(self, name, percent=0, **kwargs):
        attrs = {'name': name, 'percent': D(percent)}
        attrs.update(kwargs)
        return Tax.objects.language().create(**attrs)

    def create_product(self, name, kind=Product.SINGLE, unit_price=0, **kwargs):
        attrs = {'name': name, 'slug': slugify(name), 'code': slugify(name),
                 'kind': kind, 'unit_price': Money(unit_price)}
        attrs.update(kwargs)
        return Product.objects.language().create(**attrs)

    def create_attribute(self, name, choices, **kwargs):
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

    def create_review(self, product, customer, body='Lorem ipsum dolor sin', rating=5, **kwargs):
        attrs = {'product': product, 'customer': customer, 'body': body, 'rating': rating}
        attrs.update(kwargs)
        return Review.objects.language().create(**attrs)

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

    def create_flag(self, name, **kwargs):
        attrs = {'name': name, 'code': slugify(name)}
        attrs.update(kwargs)
        return Flag.objects.language().create(**kwargs)
