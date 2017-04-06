# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool
from django.utils.translation import ugettext_lazy as _

from shopit.settings import SINGLE_APPHOOK


# TODO: can be simplified into, after merging https://github.com/divio/django-cms/pull/5898
# from shopit.urls import get_urls

# def get_urls(self, page=None, language=None, **kwargs):
#     return get_urls('module')


class ShopitApphook(CMSApp):
    name = _('Shopit')

    def get_urls(self, page=None, language=None, **kwargs):
        if SINGLE_APPHOOK:
            return ['shopit.urls']
        return ['shopit.urls.shop']


class ShopitAccountApphook(CMSApp):
    name = _('Shopit Account')

    def get_urls(self, page=None, language=None, **kwargs):
        return ['shopit.urls.account']


class ShopitCategoriesApphook(CMSApp):
    name = _('Shopit Categories')

    def get_urls(self, page=None, language=None, **kwargs):
        return ['shopit.urls.categories']


class ShopitBrandsApphook(CMSApp):
    name = _('Shopit Brands')

    def get_urls(self, page=None, language=None, **kwargs):
        return ['shopit.urls.brands']


class ShopitManufacturersApphook(CMSApp):
    name = _('Shopit Manufacturers')

    def get_urls(self, page=None, language=None, **kwargs):
        return ['shopit.urls.manufacturers']


class ShopitProductsApphook(CMSApp):
    name = _('Shopit Products')

    def get_urls(self, page=None, language=None, **kwargs):
        return ['shopit.urls.products']


apphook_pool.register(ShopitApphook)

if not SINGLE_APPHOOK:
    apphook_pool.register(ShopitAccountApphook)
    apphook_pool.register(ShopitCategoriesApphook)
    apphook_pool.register(ShopitBrandsApphook)
    apphook_pool.register(ShopitManufacturersApphook)
    apphook_pool.register(ShopitProductsApphook)
