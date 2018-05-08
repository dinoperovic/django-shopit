# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.utils.module_loading import import_string
from django.utils.translation import ugettext_lazy as _
from shop.money import Money

from shopit.conf import app_settings


class ModifierCondition(object):
    """
    A base model for creating custom modifier conditions.
    """
    def __init__(self, name=None):
        self.name = name or getattr(self, 'name', self.__class__.__name__)

    def cart_item_condition(self, request, cart_item, value=None):
        """
        Returns if condition is met on a cart item.
        """
        return True

    def cart_condition(self, request, cart, value=None):
        """
        Returns if condition is met on a cart.
        """
        return True


class PriceGreaterThanCondition(ModifierCondition):
    name = _('Price greater than')

    def cart_item_condition(self, request, cart_item, value=0):
        return cart_item.line_total > Money(value)

    def cart_condition(self, request, cart, value=0):
        return cart.total > Money(value)


class PriceLessThanCondition(ModifierCondition):
    name = _('Price less than')

    def cart_item_condition(self, request, cart_item, value=0):
        return cart_item.line_total < Money(value)

    def cart_condition(self, request, cart, value=0):
        return cart.total < Money(value)


class QuantityGreaterThanCondition(ModifierCondition):
    name = _('Quantity greater than')

    def cart_item_condition(self, request, cart_item, value=0):
        return cart_item.quantity > int(value)


class QuantityLessThanCondition(ModifierCondition):
    name = _('Quantity less than')

    def cart_item_condition(self, request, cart_item, value=0):
        return cart_item.quantity < int(value)


class ModifierConditionsPool(object):
    """
    A pool that keeps all available modifier conditions.
    """
    def get_all_conditions(self):
        if not hasattr(self, '_all_conditions'):
            setattr(self, '_all_conditions', [import_string(path)() for path in app_settings.MODIFIER_CONDITIONS])
        return getattr(self, '_all_conditions')

    def get_condition_choices(self):
        if not hasattr(self, '_condition_choices'):
            choices = [('%s.%s' % (x.__module__, x.__class__.__name__), x.name) for x in self.get_all_conditions()]
            setattr(self, '_condition_choices', choices)
        return getattr(self, '_condition_choices')

    def get_condition(self, path):
        if path in app_settings.MODIFIER_CONDITIONS:
            for condition in self.get_all_conditions():
                if path == '%s.%s' % (condition.__module__, condition.__class__.__name__):
                    return condition


modifier_conditions_pool = ModifierConditionsPool()
