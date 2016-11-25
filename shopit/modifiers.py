# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from shop.modifiers.base import BaseCartModifier
from shop.modifiers.defaults import PayInAdvanceModifier as PayInAdvanceModifierBase
from shop.money import Money

from shopit.models.modifier import Modifier
from shopit.payment import ForwardFundPayment
from shopit.serializers import ExtraCartRow


class ShopitCartModifier(BaseCartModifier):
    """
    Applies all cart and product modifiers.
    """
    def pre_process_cart(self, cart, request):
        self.cart_discount_codes = cart.get_discount_codes().values_list('code', flat=True)

    def add_extra_cart_item_row(self, cart_item, request):
        for modifier in cart_item.product.get_modifiers():
            if modifier.can_be_applied(request, cart_item=cart_item):
                amount = modifier.get_added_amount(cart_item.line_total, cart_item.quantity)
                instance = {'label': modifier.label, 'amount': amount, 'code': self.get_applied_code(modifier)}
                cart_item.extra_rows[modifier.code] = ExtraCartRow(instance)
                cart_item.line_total += amount
                if cart_item.line_total < 0:
                    cart_item.line_total = Money(0)

    def add_extra_cart_row(self, cart, request):
        for modifier in Modifier.get_cart_modifiers():
            if modifier.can_be_applied(request, cart=cart):
                amount = modifier.get_added_amount(cart.total)
                instance = {'label': modifier.label, 'amount': amount, 'code': self.get_applied_code(modifier)}
                cart.extra_rows[modifier.code] = ExtraCartRow(instance)
                cart.total += amount
                if cart.total < 0:
                    cart.total = Money(0)

    def get_applied_code(self, modifier):
        """
        Returns first code applied to the cart, that's also a valid code
        for the given modifier. Returns `None` if modifier doesn't need a code.
        """
        discount_codes = modifier.get_discount_codes().values_list('code', flat=True)
        for code in self.cart_discount_codes:
            if code in discount_codes:
                return code


class PayInAdvanceModifier(PayInAdvanceModifierBase):
    """
    Modifier that makes use of a customized ForwardFundPayment.
    """
    payment_provider = ForwardFundPayment()
