# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from decimal import Decimal

from django.contrib.admin.sites import AdminSite
from shop.money import Money

from shopit.admin.modifier import ModifierAdmin, DiscountCodeAdmin
from shopit.models.modifier import Modifier, DiscountCode

from ..utils import ShopitTestCase


class ModifierAdminTest(ShopitTestCase):
    def setUp(self):
        self.create_request()
        self.site = AdminSite(name="admin")
        self.admin = ModifierAdmin(Modifier, self.site)

    def test_get_value(self):
        m1 = self.create_modifier('M1', amount=-10)
        m2 = self.create_modifier('M2', percent=-10)
        self.assertEquals(self.admin.get_value(m1), str(Money(-10)))
        self.assertEquals(self.admin.get_value(m2), '{} %'.format(Decimal(-10)))

    def test_get_requires_code(self):
        m1 = self.create_modifier('M1', percent=-5)
        self.create_discount_code(m1, 'code')
        self.assertTrue(self.admin.get_requires_code(m1))

    def test_get_filtering_enabled(self):
        m1 = self.create_modifier('M1', percent=-5)
        m2 = self.create_modifier('M2', percent=-10, kind=Modifier.CART)
        self.assertTrue(self.admin.get_filtering_enabled(m1))
        self.assertFalse(self.admin.get_filtering_enabled(m2))


class DiscountCodeAdminTest(ShopitTestCase):
    def setUp(self):
        self.create_request()
        self.site = AdminSite(name="admin")
        self.admin = DiscountCodeAdmin(DiscountCode, self.site)

    def test_get_is_valid(self):
        m1 = self.create_modifier('M1', percent=-5, kind=Modifier.CART)
        dc1 = self.create_discount_code(m1, 'code1')
        dc2 = self.create_discount_code(m1, 'code2', num_uses=1, max_uses=1)
        self.assertTrue(self.admin.get_is_valid(dc1))
        self.assertFalse(self.admin.get_is_valid(dc2))
