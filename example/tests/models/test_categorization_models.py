# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from filer.models.imagemodels import Image

from shopit.models.categorization import Category

from ..utils import ShopitTestCase


class CategorizationModelsTest(ShopitTestCase):
    def setUp(self):
        self.inactive_category = self.create_categorization('category', 'Inactive', active=False)

        # Modifiers
        self.phones_discount = self.create_modifier('Phones Discount 10%', percent=-10)
        self.mobile_discount = self.create_modifier('Mobile Discount 5%', percent=-5)

        # Flags
        self.f1 = self.create_flag('F1')
        self.f2 = self.create_flag('F2')

        # Tax
        self.tax = self.create_tax('PDV', percent=25)

        # Categories
        self.dummy_image = Image(original_filename='dummy.jpg')
        self.phones = self.create_categorization('category', 'Phones', tax=self.tax)
        self.phones.featured_image = self.dummy_image
        self.phones.modifiers.add(self.phones_discount)
        self.phones.flags.add(self.f1)
        self.phones_mobile = self.create_categorization('category', 'Mobile', parent=self.phones)
        self.phones_mobile.modifiers.add(self.mobile_discount)
        self.phones_mobile.flags.add(self.f2)

        self.apple = self.create_categorization('brand', 'Apple')
        self.china = self.create_categorization('manufacturer', 'Made in China')

        # Products
        self.p1 = self.create_product('P1', category=self.phones)
        self.p2 = self.create_product('P2', category=self.phones_mobile)

    def test_managers(self):
        self.assertEquals(Category.objects.active().count(), 2)

    def test__str__(self):
        self.assertEquals(str(self.phones), 'Phones')

    def test_get_absolute_url(self):
        self.assertEquals(self.phones.get_absolute_url(), '/en/shopit/categories/phones/')
        self.assertEquals(self.apple.get_absolute_url(), '/en/shopit/brands/apple/')
        self.assertEquals(self.china.get_absolute_url(), '/en/shopit/manufacturers/made-in-china/')

    def test_get_path(self):
        self.assertEquals(self.phones.get_path(), self.phones.slug)
        self.assertEquals(self.phones_mobile.get_path(), '/'.join([self.phones.slug, self.phones_mobile.slug]))

    def test_featured_image(self):
        self.assertEquals(self.phones.featured_image, self.dummy_image)
        self.assertEquals(self.phones_mobile.featured_image, self.dummy_image)

    def test_get_products(self):
        self.assertEquals(self.phones.get_products().count(), 2)
        self.assertEquals(self.phones_mobile.get_products().count(), 1)
        self.assertEquals(self.phones_mobile.get_products()[0], self.p2)

    def test_get_modifiers(self):
        self.assertEquals(self.phones.get_modifiers().count(), 1)
        self.assertEquals(self.phones_mobile.get_modifiers().count(), 2)
        self.assertEquals(self.phones_mobile.get_modifiers()[0], self.phones_discount)

    def test_flags(self):
        self.assertEquals(self.phones.get_flags().count(), 1)
        self.assertEquals(self.phones_mobile.get_flags().count(), 2)
        self.assertEquals(self.phones_mobile.get_flags()[0], self.f1)

    def test_tax(self):
        self.assertEquals(self.phones.tax, self.tax)
        self.assertEquals(self.phones_mobile.tax, self.tax)
        self.assertIsNone(self.inactive_category.tax)
