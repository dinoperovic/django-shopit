# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.core.exceptions import ValidationError

from shopit.models.cart import CartItem, CartDiscountCode
from shopit.models.modifier import Modifier

from .utils import ShopitTestCase


class ModifierTest(ShopitTestCase):
    def setUp(self):
        self.create_request()

        self.inactive_modifier = self.create_modifier('Inactive', active=False)

        self.p1 = self.create_product('Book', unit_price=1000, discountable=False)
        self.p2 = self.create_product('Phone', unit_price=500)

        # Modifiers
        self.summer = self.create_modifier('Summer added', amount=100)
        self.winter = self.create_modifier('Winter discount', percent=-10, kind=Modifier.DISCOUNT)
        self.cart_modifier = self.create_modifier('Cart mod', percent=-5, kind=Modifier.CART)

        # Discount code
        self.dc = self.create_discount_code(self.summer, 'dc1')
        self.dc_cart = self.create_discount_code(self.cart_modifier, 'dc_cart')

        # Conditions
        self.cond1 = self.create_modifier_condition(self.summer, 'shopit.modifier_conditions.QuantityGreaterThanCondition', 2)  # noqa

        # Cart item
        CartItem.objects.get_or_create(cart=self.cart, product=self.p1)
        CartItem.objects.get_or_create(cart=self.cart, product=self.p2, quantity=3)
        self.cart_items = CartItem.objects.filter_cart_items(self.cart, self.request)

    def test_managers(self):
        self.assertEquals(Modifier.objects.active().count(), 3)
        self.assertEquals(Modifier.objects.filtering_enabled().count(), 2)  # includes inactive modifier.

    def test__str__(self):
        self.assertEquals(str(self.summer), self.summer.label)

    def test_label(self):
        self.assertEquals(self.summer.label, 'Summer added')

    def test_requires_code(self):
        self.assertTrue(self.summer.requires_code)
        self.assertFalse(self.winter.requires_code)

    def test_is_filtering_enabled(self):
        self.assertFalse(self.summer.is_filtering_enabled)
        self.assertTrue(self.winter.is_filtering_enabled)

    def test_get_conditions(self):
        self.assertEquals(len(self.summer.get_conditions()), 1)

    def test_get_discount_codes(self):
        self.assertEquals(self.summer.get_discount_codes()[0], self.dc)

    def test_get_added_amount(self):
        self.assertEquals(self.summer.get_added_amount(200), 100)
        self.assertEquals(self.winter.get_added_amount(200), -20)

    def test_can_be_applied(self):
        # Can't be applied when neither `cart_item` or `cart` passed in.
        self.assertFalse(self.summer.can_be_applied(self.request))
        # Can't be applied since p1 is not eligible for winter.
        self.assertFalse(self.winter.can_be_applied(self.request, cart_item=self.cart_items[0]))
        # Can't be applied since it has condition that's not met.
        self.assertFalse(self.summer.can_be_applied(self.request, cart_item=self.cart_items[0]))
        # Can't be applied since it requires code that's not on cart.
        self.assertFalse(self.cart_modifier.can_be_applied(self.request, cart=self.cart))
        # Apply code and test again.
        CartDiscountCode.objects.create(cart=self.cart, code=self.dc_cart)
        self.assertTrue(self.cart_modifier.can_be_applied(self.request, cart=self.cart))
        # Can't be applied since it's inactive
        self.assertFalse(self.inactive_modifier.can_be_applied(self.request, cart_item=self.cart_items[0]))
        # Apply last code and test that a valid modifier can be applied.
        CartDiscountCode.objects.create(cart=self.cart, code=self.dc)
        self.assertTrue(self.summer.can_be_applied(self.request, cart_item=self.cart_items[1]))

    def test_is_eligible_product(self):
        self.assertTrue(self.summer.is_eligible_product(self.p1))
        self.assertFalse(self.winter.is_eligible_product(self.p1))

    def test_is_code_applied(self):
        CartDiscountCode.objects.create(cart=self.cart, code=self.dc)
        self.assertTrue(self.summer.is_code_applied(self.cart.id))
        self.assertFalse(self.winter.is_code_applied(self.cart.id))

    def test_clean(self):
        self.assertRaises(ValidationError, Modifier(code='negative', amount=1, kind=Modifier.DISCOUNT).clean)

    def test_get_cart_modifiers(self):
        self.assertEquals(Modifier.get_cart_modifiers().count(), 1)
        self.assertEquals(Modifier.get_cart_modifiers()[0], self.cart_modifier)
