# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.core.exceptions import ValidationError

from shopit.forms.shop import CartDiscountCodeForm

from ..utils import ShopitTestCase


class CartDiscountCodeFormTest(ShopitTestCase):
    def setUp(self):
        self.create_request()

    def test__init__(self):
        try:
            form = CartDiscountCodeForm(cart=self.request.cart)
        except:  # noqa
            self.fail("`CartDiscountCodeForm` failed to initialize.")
        self.assertFalse(form.fields['code'].required)

    def test_clean(self):
        pass
