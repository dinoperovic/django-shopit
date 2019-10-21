# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from shop.models.customer import BaseCustomer


@python_2_unicode_compatible
class Customer(BaseCustomer):
    SALUTATION = [
        ('mrs', _("Mrs.")),
        ('mr', _("Mr.")),
        ('na', _("(n/a)")),
    ]

    number = models.PositiveIntegerField(
        _('Customer Number'),
        null=True,
        default=None,
        unique=True,
    )

    salutation = models.CharField(
        _('Salutation'),
        max_length=5,
        choices=SALUTATION,
    )

    phone_number = models.CharField(
        _('Phone number'),
        max_length=255,
        blank=True,
    )

    class Meta:
        db_table = 'shopit_customers'
        verbose_name = _('Customer')
        verbose_name_plural = _('Customers')

    def __str__(self):
        return self.get_username()

    def get_number(self):
        return self.number

    def get_or_assign_number(self):
        if self.number is None:
            aggr = Customer.objects.filter(number__isnull=False).aggregate(models.Max('number'))
            self.number = (aggr['number__max'] or 0) + 1
            self.save()
        return self.get_number()

    def get_discount_codes(self):
        if not hasattr(self, '_discount_codes'):
            setattr(self, '_discount_codes', self.discount_codes.valid())
        return getattr(self, '_discount_codes')
