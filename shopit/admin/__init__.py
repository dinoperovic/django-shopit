# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from shopit.admin.customer import CustomerAdmin
from shopit.admin.order import OrderAdmin
from shopit.admin.tax import TaxAdmin
from shopit.admin.modifier import ModifierAdmin, DiscountCodeAdmin
from shopit.admin.flag import FlagAdmin
from shopit.admin.categorization import CategoryAdmin, BrandAdmin, ManufacturerAdmin
from shopit.admin.product import AttributeAdmin, ProductAdmin


__all__ = ['CustomerAdmin', 'OrderAdmin', 'TaxAdmin', 'ModifierAdmin', 'DiscountCodeAdmin', 'FlagAdmin',
           'CategoryAdmin', 'BrandAdmin', 'ManufacturerAdmin', 'AttributeAdmin', 'ProductAdmin']
