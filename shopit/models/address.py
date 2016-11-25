# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from shop.models.address import ISO_3166_CODES, BaseBillingAddress, BaseShippingAddress


class AddressModelMixin(models.Model):
    name = models.CharField(_('Full name'), max_length=1024)
    address1 = models.CharField(_('Address line 1'), max_length=1024)
    address2 = models.CharField(_('Address line 2'), max_length=1024, blank=True, null=True)
    zip_code = models.CharField(_('ZIP / Postal code'), max_length=12)
    city = models.CharField(_('City'), max_length=1024)
    country = models.CharField(_('Country'), max_length=3, choices=ISO_3166_CODES)

    class Meta:
        abstract = True

    @property
    def label(self):
        fields = [self.name, self.address1, self.address2, self.zip_code, self.city,
                  str(dict(ISO_3166_CODES)[self.country])]
        return ', '.join([x for x in fields if x])


@python_2_unicode_compatible
class ShippingAddress(BaseShippingAddress, AddressModelMixin):
    class Meta:
        db_table = 'shopit_shipping_addresses'
        verbose_name = _('Shipping address')
        verbose_name_plural = _('Shipping addresses')

    def __str__(self):
        return self.label


@python_2_unicode_compatible
class BillingAddress(BaseBillingAddress, AddressModelMixin):
    class Meta:
        db_table = 'shopit_billing_addresses'
        verbose_name = _('Billing address')
        verbose_name_plural = _('Billing addresses')

    def __str__(self):
        return self.label
