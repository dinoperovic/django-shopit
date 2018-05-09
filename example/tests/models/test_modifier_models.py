# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware
from django.utils.translation import ugettext_lazy as _
from shop.money import Money

from shopit.models.cart import CartDiscountCode, CartItem
from shopit.models.modifier import DiscountCode, Modifier, ModifierCondition
from shopit.modifier_conditions import QuantityGreaterThanCondition

from ..utils import ShopitTestCase


class ModifierModelTest(ShopitTestCase):
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


class ModifierConditionModelTest(ShopitTestCase):
    def setUp(self):
        self.create_request()

        self.mod1 = self.create_modifier('Mod1', percent=-10)
        self.cond1 = self.create_modifier_condition(self.mod1, 'shopit.modifier_conditions.QuantityGreaterThanCondition', 2)  # noqa
        self.cond2 = self.create_modifier_condition(self.mod1, 'shopit.modifier_conditions.PriceGreaterThanCondition', 10)  # noqa
        self.p1 = self.create_product('P1', unit_price=20)

        CartItem.objects.get_or_create(cart=self.cart, product=self.p1, quantity=1)
        self.cart_items = CartItem.objects.filter_cart_items(self.cart, self.request)

        self.cart.total = Money(sum([x.product.get_price(self.request) * x.quantity for x in self.cart_items]))

    def test__str__(self):
        self.assertEquals(str(self.cond1), '%s %s' % (_('Quantity greater than'), self.cond1.value))

    def test_is_met(self):
        # No cart_item or cart is True.
        self.assertTrue(self.cond1.is_met(self.request))
        # Not met since it requires more that 2 quantity
        self.assertFalse(self.cond1.is_met(self.request, cart_item=self.cart_items[0]))
        # Met since total is greater than 10.
        self.assertTrue(self.cond2.is_met(self.request, cart=self.cart))
        # Add to cart and check first again. Should be True now.
        CartItem.objects.get_or_create(cart=self.cart, product=self.p1, quantity=3)
        new_items = CartItem.objects.filter_cart_items(self.cart, self.request)
        self.assertTrue(self.cond1.is_met(self.request, cart_item=new_items[0]))

    def test_clean(self):
        self.assertRaises(ValidationError, ModifierCondition(modifier=self.mod1).clean)

    def test_condition(self):
        self.assertIsInstance(self.cond1.condition, QuantityGreaterThanCondition)


class DiscountCodeModelTest(ShopitTestCase):
    def setUp(self):
        self.mod1 = self.create_modifier('Mod1', percent=-10, kind=Modifier.DISCOUNT)
        self.inactive_dc = self.create_discount_code(self.mod1, 'Inactive DC', active=False)
        self.invalid_dc = self.create_discount_code(self.mod1, 'Invalid DC', valid_until=make_aware(parse_datetime('2018-01-01 00:00:00')))  # noqa
        self.dc1 = self.create_discount_code(self.mod1, 'dc1', valid_from=make_aware(parse_datetime('2018-05-01 00:00:00')))  # noqa
        self.dc2 = self.create_discount_code(self.mod1, 'dc2', max_uses=1)

    def test_managers(self):
        self.assertEquals(DiscountCode.objects.active().count(), 3)
        self.assertEquals(DiscountCode.objects.valid(include_added=True).count(), 2)
        self.dc2.use()
        self.assertEquals(DiscountCode.objects.valid().count(), 1)

    def test__str__(self):
        self.assertEquals(str(self.dc1), 'dc1')

    def test_is_valid(self):
        self.assertFalse(self.inactive_dc.is_valid)
        self.assertFalse(self.invalid_dc.is_valid)
        self.assertTrue(self.dc1.is_valid)
        self.assertTrue(self.dc2.is_valid)
        self.dc2.use()
        self.assertFalse(self.dc2.is_valid)

    def test_use(self):
        self.assertEquals(self.dc1.num_uses, 0)
        self.dc1.use(2)
        self.assertEquals(self.dc1.num_uses, 2)
