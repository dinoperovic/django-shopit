# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.core.urlresolvers import reverse
from shop.payment.defaults import ForwardFundPayment as ForwardFundPaymentBase


class ForwardFundPayment(ForwardFundPaymentBase):
    """
    Modified ForwardFundPayment to use regular javascript to redirect,
    instead of angularJS.
    """
    def get_payment_request(self, cart, request):
        super(ForwardFundPayment, self).get_payment_request(cart, request)
        return 'window.location.href="{}";'.format(reverse('shopit-thanks'))
