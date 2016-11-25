# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from shopit.views.shop import CartView, WatchView, CheckoutView, ThanksView
from shopit.views.account import (AccountLoginView, AccountLogoutView, AccountRegisterView, AccountResetView,
                                  AccountResetConfirmView, AccountDetailView, AccountOrderView, AccountSettingsView)
from shopit.views.product import ProductListView, ProductDetailView,  AddToCartView
from shopit.views.categorization import (CategoryListView, BrandListView, ManufacturerListView,
                                         CategoryDetailView, BrandDetailView, ManufacturerDetailView)


__all__ = ['CartView', 'WatchView', 'CheckoutView', 'ThanksView', 'AccountLoginView', 'AccountLogoutView',
           'AccountRegisterView', 'AccountResetView', 'AccountResetConfirmView', 'AccountDetailView',
           'AccountOrderView', 'AccountSettingsView', 'ProductListView', 'ProductDetailView', 'AddToCartView',
           'CategoryListView', 'BrandListView', 'ManufacturerListView',
           'CategoryDetailView', 'BrandDetailView', 'ManufacturerDetailView']
