# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.contrib.auth.models import AnonymousUser

from shopit.forms.account import AccountDetailsForm, AccountPasswordForm, AccountRegisterForm
from shopit.models.customer import Customer

from ..utils import ShopitTestCase


class AccountRegisterFormTest(ShopitTestCase):
    def setUp(self):
        self.create_request()
        self.request.user = AnonymousUser()
        self.request.customer = Customer.objects.get_or_create_from_request(self.request)

    def test_save(self):
        data = {'email': 'new@example.com', 'password1': 'new12345', 'password2': 'new12345'}
        form = AccountRegisterForm(data)
        self.assertTrue(form.is_valid())
        customer = form.save(self.request)
        self.assertEquals(Customer.objects.all().count(), 2)  # 1 already exists so 2 is expected.
        self.assertEquals(self.request.user, customer.user)
        self.assertTrue(self.request.customer.is_authenticated())

    def test_clean_email(self):
        # Use existing email.
        data = {'email': 'user@example.com', 'password1': 'new12345', 'password2': 'new12345'}
        form = AccountRegisterForm(data)
        self.assertFalse(form.is_valid())


class AccountDetailsFormTest(ShopitTestCase):
    def setUp(self):
        self.create_request()

    def test__init__(self):
        try:
            form = AccountDetailsForm(request=self.request)
        except:  # noqa
            self.fail("`AccountDetailsForm` failed to initialize.")
        self.assertEquals(form.initial['email'], 'user@example.com')
        self.assertTrue(form.fields['phone_number'].required)

    def test_save(self):
        data = {'salutation': 'mr', 'first_name': 'John', 'last_name': 'Doe',
                'email': self.request.user.email, 'phone_number': '+385993333444'}
        form = AccountDetailsForm(data, request=self.request)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEquals(self.request.customer.salutation, 'mr')
        self.assertEquals(self.request.user.first_name, 'John')
        self.assertEquals(self.request.user.last_name, 'Doe')


class AccountPasswordFormTest(ShopitTestCase):
    def setUp(self):
        self.create_request()

    def test__init__(self):
        try:
            AccountPasswordForm(request=self.request)
        except:  # noqa
            self.fail("`AccountPasswordForm` failed to initialize.")

    def test_save(self):
        data = {'old_password': 'resu', 'new_password1': 'new12345', 'new_password2': 'new12345'}
        form = AccountPasswordForm(data, request=self.request)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertTrue(self.request.user.check_password('new12345'))
