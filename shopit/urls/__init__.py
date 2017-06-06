# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.conf.urls import url
from django.utils.translation import ugettext_lazy as _
from django.views.generic import RedirectView

from shopit import views
from shopit.settings import SINGLE_APPHOOK


def get_urls(name, prefixed=SINGLE_APPHOOK):  # noqa
    """
    Returns url patterns for the given module.
    Checks if urls are handled with single or multiple apphooks.
    """
    pk_regexp = r'(?P<pk>\d+)'
    slug_regexp = r'(?P<slug>[-_\w\d]+)'
    path_regexp = r'(?P<path>[-_/\w\d]+)'
    list_regexp = r'^$'
    detail_regexp = r'^%s/$' % slug_regexp

    if name == 'shop':
        cart_regexp = _(r'cart/$')
        cart_empty_regexp = _(r'cart/empty/$')
        watch_regexp = _(r'watch/$')
        checkout_regexp = _(r'checkout/$')
        thanks_regexp = _(r'thanks/$')

        if prefixed:
            list_regexp = _(r'shop/$')
            cart_regexp = _(r'shop/cart/$')
            cart_empty_regexp = _(r'shop/cart/empty/$')
            watch_regexp = _(r'shop/watch/$')
            checkout_regexp = _(r'shop/checkout/$')
            thanks_regexp = _(r'shop/thanks/$')

        return [
            url(list_regexp, RedirectView.as_view(pattern_name='shopit-cart')),
            url(cart_regexp, views.CartView.as_view(), name='shopit-cart'),
            url(cart_empty_regexp, views.CartView.as_view(empty=True), name='shopit-cart-empty'),
            url(watch_regexp, views.WatchView.as_view(), name='shopit-watch'),
            url(checkout_regexp, views.CheckoutView.as_view(), name='shopit-checkout'),
            url(thanks_regexp, views.ThanksView.as_view(), name='shopit-thanks'),
        ]

    if name == 'account':
        reset_confirm_kwargs = r'(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})'

        detail_regexp = list_regexp
        login_regexp = _(r'^login/$')
        logout_regexp = _(r'^logout/$')
        register_regexp = _(r'^register/$')
        reset_regexp = _(r'^reset/$')
        reset_confirm_regexp = _(r'^reset/confirm/%s/$') % reset_confirm_kwargs
        order_list_regexp = _(r'^orders/$')
        order_detail_regexp = _(r'^orders/%s/$') % pk_regexp
        order_latest_regexp = _(r'^orders/latest/$')
        settings_regexp = _(r'^settings/$')
        settings_details_regexp = _(r'^settings/details/$')
        settings_password_regexp = _(r'^settings/password/$')

        if prefixed:
            detail_regexp = _(r'^account/$')
            login_regexp = _(r'^account/login/$')
            logout_regexp = _(r'^account/logout/$')
            register_regexp = _(r'^account/register/$')
            reset_regexp = _(r'^account/reset/$')
            reset_confirm_regexp = _(r'^account/reset/confirm/%s/$') % reset_confirm_kwargs
            order_list_regexp = _(r'^account/orders/$')
            order_detail_regexp = _(r'^account/orders/%s/$') % pk_regexp
            order_latest_regexp = _(r'^account/orders/latest/$')
            settings_regexp = _(r'^account/settings/$')
            settings_details_regexp = _(r'^account/settings/details/$')
            settings_password_regexp = _(r'^account/settings/password/$')

        return [
            url(detail_regexp, views.AccountDetailView.as_view(), name='shopit-account-detail'),
            url(login_regexp, views.AccountLoginView.as_view(), name='shopit-account-login'),
            url(logout_regexp, views.AccountLogoutView.as_view(), name='shopit-account-logout'),
            url(register_regexp, views.AccountRegisterView.as_view(), name='shopit-account-register'),
            url(reset_regexp, views.AccountResetView.as_view(), name='shopit-account-reset'),
            url(reset_confirm_regexp, views.AccountResetConfirmView.as_view(), name='shopit-account-reset-confirm'),
            url(order_list_regexp, views.AccountOrderView.as_view(), name='shopit-account-order-list'),
            url(order_detail_regexp, views.AccountOrderView.as_view(many=False), name='shopit-account-order-detail'),
            url(order_latest_regexp, views.AccountOrderView.as_view(latest=True), name='shopit-account-order-latest'),
            url(settings_regexp, views.AccountSettingsView.as_view(), name='shopit-account-settings'),
            url(settings_details_regexp, views.AccountSettingsView.as_view(action='details'),
                name='shopit-account-settings-details'),
            url(settings_password_regexp, views.AccountSettingsView.as_view(action='password'),
                name='shopit-account-settings-password'),
        ]

    if name == 'categories':
        detail_regexp = r'^%s/$' % path_regexp

        if prefixed:
            list_regexp = _(r'^categories/$')
            detail_regexp = _(r'^categories/%s/$') % path_regexp

        return [
            url(list_regexp, views.CategoryListView.as_view(), name='shopit-category-list'),
            url(detail_regexp, views.CategoryDetailView.as_view(), name='shopit-category-detail'),
        ]

    if name == 'brands':
        detail_regexp = r'^%s/$' % path_regexp

        if prefixed:
            list_regexp = _(r'^brands/$')
            detail_regexp = _(r'^brands/%s/$') % path_regexp

        return [
            url(list_regexp, views.BrandListView.as_view(), name='shopit-brand-list'),
            url(detail_regexp, views.BrandDetailView.as_view(), name='shopit-brand-detail'),
        ]

    if name == 'manufacturers':
        detail_regexp = r'^%s/$' % path_regexp

        if prefixed:
            list_regexp = _(r'^manufacturers/$')
            detail_regexp = _(r'^manufacturers/%s/$') % path_regexp

        return [
            url(list_regexp, views.ManufacturerListView.as_view(), name='shopit-manufacturer-list'),
            url(detail_regexp, views.ManufacturerDetailView.as_view(), name='shopit-manufacturer-detail'),
        ]

    if name == 'products':
        review_regexp = _(r'^%s/reviews/$') % slug_regexp
        add_to_cart_regexp = _(r'^%s/add-to-cart/$') % slug_regexp

        if prefixed:
            list_regexp = _(r'^products/$')
            detail_regexp = _(r'^products/%s/$') % slug_regexp
            add_to_cart_regexp = _(r'^products/%s/add-to-cart/$') % slug_regexp
            review_regexp = _(r'^products/%s/reviews/$') % slug_regexp

        return [
            url(list_regexp, views.ProductListView.as_view(), name='shopit-product-list'),
            url(detail_regexp, views.ProductDetailView.as_view(), name='shopit-product-detail'),
            url(review_regexp, views.ProductReviewListCreateView.as_view(), name='shopit-product-review-list-create'),
            url(add_to_cart_regexp, views.AddToCartView.as_view(), name='shopit-add-to-cart'),
        ]


urlpatterns = []
for name in ('shop', 'account', 'categories', 'brands', 'manufacturers', 'products'):
    urlpatterns.extend(get_urls(name, prefixed=True))
