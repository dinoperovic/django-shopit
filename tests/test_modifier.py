# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from decimal import Decimal as D

from django.test import TestCase
from django.utils.text import slugify
from shop.money import Money

from shopit.models.product import Modifier, Product

from .test_product import create_product


def create_modifier(name, amount=0, percent=None, **kwargs):
    attrs = {
        'name': name,
        'code': slugify(name),
        'amount': Money(amount),
        'percent': D(percent) if percent else None,
    }
    attrs.update(kwargs)
    return Modifier.objects.language().create(**attrs)


class TestModifier(TestCase):
    def setUp(self):
        self.p1 = create_product('P1', Product.SINGLE, 1000, discountable=False)
        self.mod1 = create_modifier('Summer added', amount=100)
        self.mod2 = create_modifier('Winter discount', percent=-10, kind=Modifier.DISCOUNT)

    def test__label(self):
        self.assertEquals(self.mod1.label, 'Summer added')

    def test_get_added_amount(self):
        self.assertEquals(self.mod1.get_added_amount(200), 100)
        self.assertEquals(self.mod2.get_added_amount(200), -20)

    def test_is_eligible_product(self):
        self.assertTrue(self.mod1.is_eligible_product(self.p1))
        self.assertFalse(self.mod2.is_eligible_product(self.p1))
