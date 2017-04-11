# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django import forms
from django.contrib.auth import authenticate, get_user_model, login, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from shopit.models.customer import Customer


class CleanEmailMixin(object):
    """
    Mixin used in forms where customers email is modified or created.
    Checks that email doesn't already exists.
    """
    def clean_email(self):
        email = self.cleaned_data['email']
        if 'email' in self.changed_data and get_user_model().objects.filter(is_active=True, email=email).exists():
            raise ValidationError(_('An account with this email address already exists.'))
        return email


class AccountLoginForm(AuthenticationForm):
    """
    Override username to be an email field, to disallow username logins.
    """
    username = forms.EmailField(label=_('Email address'))


class AccountRegisterForm(CleanEmailMixin, UserCreationForm):
    email = forms.EmailField(label=_('Email address'))

    class Meta:
        model = Customer
        fields = ['email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        # Override default init from `UserCreationForm` to use email as
        # username field, and set autofocus.
        super(UserCreationForm, self).__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({'autofocus': ''})

    def save(self, request, commit=False):
        self.instance = Customer.objects.get_from_request(request)
        self.instance.recognize_as_registered()
        self.instance.user.is_active = True
        self.instance.user.email = self.cleaned_data['email']
        password = self.cleaned_data['password1']
        self.instance.user.set_password(password)
        self.instance.save()
        user = authenticate(username=self.instance.user.username, password=password)
        login(request, user)
        return self.instance


class AccountDetailsForm(CleanEmailMixin, forms.ModelForm):
    first_name = forms.CharField(label=_('First name'), max_length=30, required=False)
    last_name = forms.CharField(label=_('Last name'), max_length=30, required=False)
    email = forms.EmailField(label=_('Email address'))

    class Meta:
        model = Customer
        fields = ['salutation', 'first_name', 'last_name', 'email']
        custom_fields = ['first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        self.instance = Customer.objects.get_from_request(self.request)
        kwargs['instance'] = self.instance
        kwargs['initial'] = dict([(x, getattr(self.instance, x)) for x in self.Meta.custom_fields])
        super(AccountDetailsForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        for field in self.Meta.custom_fields:
            setattr(self.instance, field, self.cleaned_data[field])
        customer = super(AccountDetailsForm, self).save(commit)
        return customer

    def get_success_message(self):
        return _('Info successfully updated.')


class AccountPasswordForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(AccountPasswordForm, self).__init__(self.request.user, *args, **kwargs)

    def save(self, commit=True):
        user = super(AccountPasswordForm, self).save(commit)
        update_session_auth_hash(self.request, user)
        return user

    def get_success_message(self):
        return _('Password successfully changed.')
