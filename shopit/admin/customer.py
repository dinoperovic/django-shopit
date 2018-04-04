# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.contrib import admin
from shop.admin.customer import CustomerAdminBase, CustomerInlineAdminBase, CustomerProxy


class CustomerInlineAdmin(CustomerInlineAdminBase):
    readonly_fields = ['get_number', 'salutation', 'phone_number']
    fieldsets = [(None, {'fields': ['get_number', 'salutation', 'phone_number']})]


@admin.register(CustomerProxy)
class CustomerAdmin(CustomerAdminBase):
    inlines = [CustomerInlineAdmin]
