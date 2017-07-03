# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from shop.models.cart import BaseCart, BaseCartItem

from shopit.models.address import BillingAddress, ShippingAddress


@python_2_unicode_compatible
class Cart(BaseCart):
    shipping_address = models.ForeignKey(ShippingAddress, null=True, default=None, related_name='+')
    billing_address = models.ForeignKey(BillingAddress, null=True, default=None, related_name='+')

    class Meta:
        db_table = 'shopit_carts'
        verbose_name = _('Shopping cart')
        verbose_name_plural = _('Shopping carts')

    def __str__(self):
        return str(self.pk)

    def get_discount_codes(self):
        if not hasattr(self, '_discount_codes'):
            setattr(self, '_discount_codes', self.discount_codes.all())
        return getattr(self, '_discount_codes')


@python_2_unicode_compatible
class CartItem(BaseCartItem):
    quantity = models.IntegerField(validators=[MinValueValidator(0)])

    class Meta:
        db_table = 'shopit_cart_items'
        verbose_name = _('Cart item')
        verbose_name_plural = _('Cart items')

    def __str__(self):
        return self.product.product_name


@python_2_unicode_compatible
class CartDiscountCode(models.Model):
    """
    Discount codes that are added to the cart.
    """
    cart = models.ForeignKey(Cart, models.SET_NULL, null=True, related_name='discount_codes', editable=False)
    code = models.CharField(_('Code'), max_length=30)

    class Meta:
        db_table = 'shopit_cart_discount_codes'
        verbose_name = _('Cart discount code')
        verbose_name_plural = _('Cart discount codes')

    def __str__(self):
        return self.code
