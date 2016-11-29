# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from .utils import ShopitTestCase


class CategorizationTest(ShopitTestCase):
    def setUp(self):
        self.phones = self.create_categorization('category', 'Phones')
        self.apple = self.create_categorization('brand', 'Apple')
        self.china = self.create_categorization('manufacturer', 'Made in China')

    def test__str__(self):
        self.assertEquals(str(self.phones), 'Phones')

    def test_get_absolute_url(self):
        self.assertEquals(self.phones.get_absolute_url(), '/en/shopit/categories/phones/')
        self.assertEquals(self.apple.get_absolute_url(), '/en/shopit/brands/apple/')
        self.assertEquals(self.china.get_absolute_url(), '/en/shopit/manufacturers/made-in-china/')
