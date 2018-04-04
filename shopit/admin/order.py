# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.contrib import admin
from shop.admin.delivery import DeliveryOrderAdminMixin
from shop.admin.order import OrderAdmin as OrderAdminBase
from shop.admin.order import PrintOrderAdminMixin

from shopit.models.order import Order


@admin.register(Order)
class OrderAdmin(PrintOrderAdminMixin, DeliveryOrderAdminMixin, OrderAdminBase):
    class Media:
        css = {'all': ['shopit/css/djangocms-admin-style.css']}
