# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from shopit.models.modifier import Modifier

from .utils import ShopitTestCase


class ModifierTest(ShopitTestCase):
    def setUp(self):
        self.book = self.create_product('Book', unit_price=1000, discountable=False)
        self.summer = self.create_modifier('Summer added', amount=100)
        self.winter = self.create_modifier('Winter discount', percent=-10, kind=Modifier.DISCOUNT)

    def test_label(self):
        self.assertEquals(self.summer.label, 'Summer added')

    def test_get_added_amount(self):
        self.assertEquals(self.summer.get_added_amount(200), 100)
        self.assertEquals(self.winter.get_added_amount(200), -20)

    def test_is_eligible_product(self):
        self.assertTrue(self.summer.is_eligible_product(self.book))
        self.assertFalse(self.winter.is_eligible_product(self.book))
