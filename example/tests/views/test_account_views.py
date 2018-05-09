# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core import mail
from django.core.urlresolvers import reverse

from shopit.models.customer import Customer

from ..utils import ShopitTestCase


class AccountViewsTest(ShopitTestCase):
    def setUp(self):
        self.dino = self.create_customer('dino', password='secret')

    def login(self, customer, password=None):
        if not password:
            password = customer._password
        return self.client.post(reverse('shopit-account-login'), {
            'username': customer.get_username(),
            'password': password,
        })

    def test_login(self):
        url = reverse('shopit-account-login')
        self.assertEquals(self.client.get(url).status_code, 200)
        response = self.client.post(url, {'username': 'dino', 'password': 'invalid'})
        self.assertEquals(response.status_code, 400)
        self.assertEquals(self.login(self.dino).status_code, 200)
        response = self.client.get(url)
        self.assertEquals(response.status_code, 302)
        self.assertEquals(response.url, reverse('shopit-account-detail'))

    def test_logout(self):
        response = self.login(self.dino)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.dino.user.pk)
        response = self.client.get(reverse('shopit-account-logout'))
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertEquals(response.status_code, 302)
        self.assertEquals(response.url, reverse('shopit-account-login'))

    def test_reset(self):
        url = reverse('shopit-account-reset')
        self.assertEquals(self.client.get(url).status_code, 200)
        response = self.client.post(url, {'email': self.dino.email})
        self.assertEquals(response.status_code, 200)
        self.assertEquals(len(mail.outbox), 1)
        url = reverse('shopit-account-reset-confirm', kwargs={
            'uidb64': response.context['uid'],
            'token': response.context['token'],
        })
        self.assertTrue(self.client.get(url).context['validlink'])
        password = 'new-secret'
        response = self.client.post(url, {'new_password1': password, 'new_password2': password})
        self.assertEquals(response.status_code, 200)
        self.assertEquals(self.login(self.dino, password=password).status_code, 200)
        self.dino._password = password  # store new password.

    def test_register(self):
        url = reverse('shopit-account-register')
        self.assertEquals(self.client.get(url).status_code, 200)
        kwargs = {
            'email': 'john@example.com',
            'password1': 'supersecretpassword',
            'password2': 'wrong',
        }
        self.assertEquals(self.client.post(url, kwargs).status_code, 400)
        kwargs['password2'] = 'supersecretpassword'
        self.assertEquals(self.client.post(url, kwargs).status_code, 200)
        new_customer = Customer.objects.get(email=kwargs['email'])
        new_customer._password = kwargs['password1']
        self.assertEqual(int(self.client.session['_auth_user_id']), new_customer.pk)

    def test_detail(self):
        url = reverse('shopit-account-detail')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 302)
        login_url = '%s?next=%s' % (reverse('shopit-account-login'), url)
        self.assertEquals(response.url, login_url)
        self.login(self.dino)
        self.assertEquals(self.client.get(url).status_code, 200)
