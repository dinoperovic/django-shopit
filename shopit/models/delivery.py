# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from shop.models.delivery import BaseDelivery, BaseDeliveryItem


@python_2_unicode_compatible
class Delivery(BaseDelivery):
    class Meta:
        db_table = 'shopit_deliveries'
        verbose_name = _('Delivery')
        verbose_name_plural = _('Deliveries')

    def __str__(self):
        return str(self.pk)


@python_2_unicode_compatible
class DeliveryItem(BaseDeliveryItem):
    quantity = models.IntegerField(_('Delivered quantity'), default=0)

    class Meta:
        db_table = 'shopit_delivery_items'
        verbose_name = _('Delivery item')
        verbose_name_plural = _('Delivery items')

    def __str__(self):
        return self.item.product_name
