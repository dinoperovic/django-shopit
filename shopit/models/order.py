# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.core.urlresolvers import NoReverseMatch, reverse
from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django_fsm import transition
from shop.models.order import BaseOrder, BaseOrderItem
from shop.models.order import OrderManager as OrderManagerBase


class OrderManager(OrderManagerBase):
    def get_summary_url(self):
        try:
            return reverse('shopit-account-order-list')
        except NoReverseMatch:
            return super(OrderManager, self).get_summary_url()

    def get_latest_url(self):
        try:
            return reverse('shopit-account-order-latest')
        except NoReverseMatch:
            return reverse('shopit-thanks')
        except NoReverseMatch:
            return super(OrderManager, self).get_latest_url()


@python_2_unicode_compatible
class Order(BaseOrder):
    number = models.PositiveIntegerField(
        _("Order Number"),
        null=True,
        default=None,
        unique=True,
    )

    shipping_address_text = models.TextField(
        _("Shipping Address"),
        blank=True,
        null=True,
        help_text=_('Shipping address at the moment of purchase.'),
    )

    billing_address_text = models.TextField(
        _("Billing Address"),
        blank=True,
        null=True,
        help_text=_('Billing address at the moment of purchase.'),
    )

    objects = OrderManager()

    class Meta:
        db_table = 'shopit_orders'
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')

    def __str__(self):
        return self.get_number() if self.number else str(self.pk)

    def get_absolute_url(self):
        try:
            return reverse('shopit-account-order-detail', args=[self.pk])
        except NoReverseMatch:
            pass

    def get_or_assign_number(self):
        """
        Set a unique number to identify this Order object. The first 4 digits
        represent the current year. The last five digits represent a
        zero-padded incremental counter.
        """
        if self.number is None:
            epoch = timezone.now().date()
            epoch = epoch.replace(epoch.year, 1, 1)
            aggr = Order.objects.filter(number__isnull=False, created_at__gt=epoch).aggregate(models.Max('number'))
            try:
                epoc_number = int(str(aggr['number__max'])[4:]) + 1
                self.number = int('{0}{1:05d}'.format(epoch.year, epoc_number))
            except (KeyError, ValueError):
                # the first order this year
                self.number = int('{0}00001'.format(epoch.year))
        return self.get_number()

    def get_number(self):
        return str(self.number)[:4] + '-' + str(self.number)[4:]

    @classmethod
    def resolve_number(cls, number):
        number = number[:4] + number[5:]
        return dict(number=number)

    def populate_from_cart(self, cart, request):
        self.shipping_address_text = cart.shipping_address.as_text() if cart.shipping_address else ''
        self.billing_address_text = cart.billing_address.as_text() if cart.billing_address else ''

        # in case one of the addresses was None, the customer presumably intended the other one.
        if not self.shipping_address_text:
            self.shipping_address_text = self.billing_address_text
        if not self.billing_address_text:
            self.billing_address_text = self.shipping_address_text
        super(Order, self).populate_from_cart(cart, request)

    def is_fully_paid(self):
        return super(Order, self).is_fully_paid()

    @transition(field='status', source='*', target='payment_confirmed', conditions=[is_fully_paid],
                custom=dict(admin=False))
    def acknowledge_payment(self, by=None):
        """
        This is here only to force setting `admin=False` to hide the
        button in admin.
        """


@python_2_unicode_compatible
class OrderItem(BaseOrderItem):
    quantity = models.IntegerField(_('Ordered quantity'))

    canceled = models.BooleanField(
        _('Item canceled'),
        default=False,
    )

    class Meta:
        db_table = 'shopit_order_items'
        verbose_name = _('Order item')
        verbose_name_plural = _('Order items')

    def __str__(self):
        return self.product_name

    def populate_from_cart_item(self, cart_item, request):
        self.product_code = cart_item.product.product_code
        super(OrderItem, self).populate_from_cart_item(cart_item, request)
