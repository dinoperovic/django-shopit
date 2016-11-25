# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from datetime import datetime
from decimal import Decimal as D

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils.text import slugify
from shop.money import Money

from shopit.models.product import Product
from shopit.models.tax import Tax


def create_product(name, kind=Product.SINGLE, unit_price=0, **kwargs):
    attrs = {
        'name': name,
        'slug': slugify(name),
        'code': slugify(name),
        'unit_price': Money(unit_price),
        'kind': kind,
    }
    attrs.update(kwargs)
    return Product.objects.language().create(**attrs)


def create_tax(name, percent=0, **kwargs):
    attrs = {'name': name, 'percent': D(percent)}
    attrs.update(kwargs)
    return Tax.objects.language().create(**attrs)


class ProductManagerTest(TestCase):
    def setUp(self):
        self.p1 = create_product('P1', Product.SINGLE, 100)
        self.p2 = create_product('P2', Product.GROUP, 100)
        self.p3 = create_product('P3', Product.VARIANT, 100, group=self.p2)

    def test_active(self):
        self.assertEquals(Product.objects.active().count(), 3)

    def test_top_level(self):
        self.assertEquals([self.p2, self.p1], list(Product.objects.top_level()))


class ProductTest(TestCase):
    def setUp(self):
        self.tax = create_tax('Default Tax', 10)
        self.p1 = create_product('P1', Product.SINGLE, 100)
        self.p2 = create_product('P2', Product.SINGLE, 100, tax=self.tax)
        self.p3 = create_product('P3', Product.SINGLE, 300)
        self.iphone = create_product('iPhone', Product.GROUP, 500)
        self.iphone_gold = create_product('iPhone Gold', Product.VARIANT, 600, group=self.iphone)
        self.iphone_black = create_product('iPhone Black', Product.VARIANT, group=self.iphone, discount=10)

    def test__str__(self):
        self.assertEquals(str(self.p1), 'P1')

    def test_get_absolute_url(self):
        self.assertEquals(self.p1.get_absolute_url(), '/en/shopit/products/p1/')

    def test_save(self):
        self.assertFalse(self.p3.is_group)
        var = create_product('P3 var', Product.VARIANT, group=self.p3)
        p3 = Product.objects.get(pk=self.p3.pk)
        self.assertTrue(p3.is_group)
        self.assertEquals(p3.order, var.order)
        self.iphone.save()
        for var in self.iphone.get_variants():
            self.assertEquals(var.order, self.iphone.order)

    def test_product_name(self):
        self.assertEquals(self.p1.product_name, 'P1')

    def test_product_code(self):
        self.assertEquals(self.p1.product_code, 'p1')

    def test_category(self):
        self.p1.category = None
        self.assertIsNone(self.p1.category)

    def test_brand(self):
        self.p1.brand = None
        self.assertIsNone(self.p1.brand)

    def test_manufacturer(self):
        self.p1.manufacturer = None
        self.assertIsNone(self.p1.manufacturer)

    def test_is_single(self):
        self.assertTrue(self.p1.is_single)
        self.assertFalse(self.iphone.is_single)

    def test_is_group(self):
        self.assertFalse(self.p1.is_group)
        self.assertTrue(self.iphone.is_group)

    def test_is_variant(self):
        self.assertFalse(self.p1.is_variant)
        self.assertTrue(self.iphone_gold.is_variant)

    def test_is_discounted(self):
        self.assertFalse(self.p1.is_discounted)
        self.assertTrue(self.iphone_black.is_discounted)

    def test_is_taxed(self):
        self.assertFalse(self.p1.is_taxed)
        self.assertTrue(self.p2.is_taxed)

    def test_get_price(self):
        self.assertEquals(self.p1.get_price(), 100)
        # discounted 500-10% = 450
        self.assertEquals(self.iphone_black.get_price(), 450)

    def test_get_availability(self):
        self.assertEquals(self.p1.get_availability(), [(True, datetime.max)])

    def test_get_attr(self):
        self.iphone_gold.get_attr('unit_price', 600)
        # returns groups unit_price 500
        self.iphone_black.get_attr('unit_price', 500)

    def test_clean(self):
        kinds = dict([(0, 'single'), (1, 'group'), (2, 'variant')])
        self.assertTrue(hasattr(self.p1, '_clean_%s' % kinds[self.p1.kind]))
        self.iphone.clean()
        # does not have a group, should fail
        self.assertRaises(ValidationError, lambda: create_product('Dirty', Product.VARIANT, 300, group=None))
