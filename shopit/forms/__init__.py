# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from shopit.forms.shop import (CartDiscountCodeForm, CustomerForm, GuestForm, ShippingAddressForm, BillingAddressForm,
                               PaymentMethodForm, DeliveryMethodForm, ExtraAnnotationForm, AcceptConditionForm)
from shopit.forms.categorization import CategoryModelForm, BrandModelForm, ManufacturerModelForm
from shopit.forms.product import (ProductModelForm, AttributeChoiceInlineFormSet, AttributeValueInlineFormSet,
                                  AttributeValueModelForm)
from shopit.forms.account import AccountLoginForm, AccountRegisterForm, AccountDetailsForm, AccountPasswordForm


__all__ = ['CartDiscountCodeForm', 'CustomerForm', 'GuestForm', 'ShippingAddressForm', 'BillingAddressForm',
           'PaymentMethodForm', 'DeliveryMethodForm', 'ExtraAnnotationForm', 'AcceptConditionForm',
           'CategoryModelForm', 'BrandModelForm', 'ManufacturerModelForm', 'ProductModelForm',
           'AttributeChoiceInlineFormSet', 'AttributeValueInlineFormSet', 'AttributeValueModelForm',
           'AccountLoginForm', 'AccountRegisterForm', 'AccountDetailsForm', 'AccountPasswordForm']
