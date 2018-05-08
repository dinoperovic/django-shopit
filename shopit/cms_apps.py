# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool
from django.utils.translation import ugettext_lazy as _

from shopit.conf import app_settings
from shopit.urls import get_urls


@apphook_pool.register
class ShopitApphook(CMSApp):
    name = _('Shopit')

    def get_urls(self, page=None, language=None, **kwargs):
        if app_settings.SINGLE_APPHOOK:
            return ['shopit.urls']
        return get_urls('shop')


class ShopitAccountApphook(CMSApp):
    name = _('Shopit Account')

    def get_urls(self, page=None, language=None, **kwargs):
        return get_urls('account')


class ShopitCategoriesApphook(CMSApp):
    name = _('Shopit Categories')

    def get_urls(self, page=None, language=None, **kwargs):
        return get_urls('categories')


class ShopitBrandsApphook(CMSApp):
    name = _('Shopit Brands')

    def get_urls(self, page=None, language=None, **kwargs):
        return get_urls('brands')


class ShopitManufacturersApphook(CMSApp):
    name = _('Shopit Manufacturers')

    def get_urls(self, page=None, language=None, **kwargs):
        return get_urls('manufacturers')


class ShopitProductsApphook(CMSApp):
    name = _('Shopit Products')

    def get_urls(self, page=None, language=None, **kwargs):
        return get_urls('products')


if not app_settings.SINGLE_APPHOOK:
    apphook_pool.register(ShopitAccountApphook)
    apphook_pool.register(ShopitCategoriesApphook)
    apphook_pool.register(ShopitBrandsApphook)
    apphook_pool.register(ShopitManufacturersApphook)
    apphook_pool.register(ShopitProductsApphook)
