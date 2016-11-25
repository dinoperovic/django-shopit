# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.utils.translation import ugettext_lazy as _
from django_fsm import transition


class ShippingWorkflowMixin(object):
    """
    A simple workflow mixin that adds a shipping state transtion to the order.
    """
    TRANSITION_TARGETS = {
        'ship_goods': _('Ship goods'),
    }

    @transition(field='status', source=['payment_confirmed'], target='ship_goods',
                custom=dict(admin=True, button_name=_('Ship the goods')))
    def ship_goods(self, by=None):
        pass
