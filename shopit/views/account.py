# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.generic import FormView
from rest_auth.registration.app_settings import RegisterSerializer
from rest_framework import status
from rest_framework.generics import RetrieveAPIView
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.settings import api_settings
from shop.views.auth import AuthFormsView, LoginView, LogoutView, PasswordResetConfirm, PasswordResetView
from shop.views.order import OrderView

from shopit.forms import account as account_forms
from shopit.models.customer import Customer
from shopit.models.order import Order
from shopit.rest.renderers import ModifiedCMSPageRenderer
from shopit.serializers import (AccountResetConfirmSerializer, AccountResetSerializer, AccountSerializer,
                                OrderListSerializer)


class LoginRegisterMixin(object):
    """
    Redirects already logged in customers to their account.
    """
    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated():
            return redirect('shopit-account-detail')
        return super(LoginRegisterMixin, self).dispatch(request, *args, **kwargs)


class AccountLoginView(LoginRegisterMixin, LoginView):
    form_class = account_forms.AccountLoginForm
    template_name = 'shopit/account/account_login.html'

    @method_decorator(never_cache)
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {'form': self.form_class()})

    def login(self):
        super(AccountLoginView, self).login()
        messages.success(self.request._request, _('You have been successfully logged in.'))

    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def post(self, request, *args, **kwargs):
        return super(AccountLoginView, self).post(request, *args, **kwargs)


class AccountLogoutView(LogoutView):
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        self.post(request, *args, **kwargs)
        messages.success(request, _('You have been successfully logged out.'))
        return redirect('shopit-account-login')


class AccountResetView(LoginRegisterMixin, PasswordResetView):
    serializer_class = AccountResetSerializer
    form_class = PasswordResetForm
    template_name = 'shopit/account/account_reset.html'

    @method_decorator(never_cache)
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {'form': self.form_class()})

    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        msg = _("Instructions on how to reset the password have been sent to '{email}'.").format(**serializer.data)
        messages.success(request._request, msg)
        return Response({'success': msg}, status=status.HTTP_200_OK)


class AccountResetConfirmView(LoginRegisterMixin, PasswordResetConfirm):
    serializer_class = AccountResetConfirmSerializer
    renderer_classes = [TemplateHTMLRenderer] + api_settings.DEFAULT_RENDERER_CLASSES
    form_class = SetPasswordForm
    template_name = 'shopit/account/account_reset_confirm.html'

    @method_decorator(never_cache)
    def get(self, request, uidb64=None, token=None):
        data = {'uid': uidb64, 'token': token}
        serializer_class = self.get_serializer_class()
        password = get_user_model().objects.make_random_password()
        data.update(new_password1=password, new_password2=password)
        serializer = serializer_class(data=data, context=self.get_serializer_context())
        if not serializer.is_valid():
            return Response({'validlink': False})
        return Response({
            'validlink': True,
            'user_name': force_text(serializer.user),
            'form': self.form_class(serializer.user),
        })

    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def post(self, request, uidb64=None, token=None):
        data = dict(list(request.data.items()), uid=uidb64, token=token)
        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        msg = _('Account has been reset with the new password.')
        messages.success(request._request, msg)
        return Response({'success': msg})


class AccountRegisterView(LoginRegisterMixin, AuthFormsView):
    serializer_class = RegisterSerializer
    form_class = account_forms.AccountRegisterForm
    template_name = 'shopit/account/account_register.html'

    @method_decorator(never_cache)
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {'form': self.form_class()})

    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def post(self, request, *args, **kwargs):
        if request.customer.is_visitor():
            request.customer = Customer.objects.get_or_create_from_request(request)
        response = super(AccountRegisterView, self).post(request, *args, **kwargs)
        if response.status_code == 200:
            messages.success(self.request._request, _('You have been successfully registered.'))
        return response


class AccountDetailView(LoginRequiredMixin, RetrieveAPIView):
    serializer_class = AccountSerializer
    renderer_classes = [ModifiedCMSPageRenderer] + api_settings.DEFAULT_RENDERER_CLASSES
    template_name = 'shopit/account/account_detail.html'

    def dispatch(self, request, *args, **kwargs):
        """
        Add exception to login required mixin when ajax GET request of a non
        visiting customer is in question. This allows to get the Anonymous
        user as JSON.
        """
        if not request.customer.is_visitor() and request.is_ajax() and request.method == 'GET':
            return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)
        return super(AccountDetailView, self).dispatch(request, *args, **kwargs)

    def get_object(self):
        return Customer.objects.get_from_request(self.request)


class AccountOrderView(LoginRequiredMixin, OrderView):
    latest = False
    renderer_classes = [ModifiedCMSPageRenderer] + api_settings.DEFAULT_RENDERER_CLASSES
    list_serializer_class = OrderListSerializer
    lookup_field = lookup_url_kwarg = 'pk'

    def dispatch(self, request, *args, **kwargs):
        """
        Redirect to latest order if needed.
        """
        if self.latest:
            latest = Order.objects.filter_from_request(request).first()
            return redirect(latest) if latest else redirect('shopit-account-order-list')
        return super(AccountOrderView, self).dispatch(request, *args, **kwargs)

    def get_renderer_context(self):
        context = super(AccountOrderView, self).get_renderer_context()
        if self.request.accepted_renderer.format == 'html':
            if self.many:
                queryset = self.filter_queryset(self.get_queryset())
                page = self.paginate_queryset(queryset)
                if page is not None:
                    context.update(self.paginator.get_html_context())
                context['order_list'] = page or queryset
            else:
                context['order'] = self.get_object()
        return context

    def get_template_names(self):
        if self.many:
            return ['shopit/account/account_order_list.html']
        return ['shopit/account/account_order_detail.html']


class AccountSettingsView(LoginRequiredMixin, FormView):
    """
    Settings view that uses different forms based on `action` property.
    Set 'action = details|password' to access different sections.
    """
    action = None

    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        return super(AccountSettingsView, self).dispatch(request, *args, **kwargs)

    def form_invalid(self, form):
        if self.request.is_ajax():
            return JsonResponse(dict(form.errors), status=400)
        return super(AccountSettingsView, self).form_invalid(form)

    def form_valid(self, form):
        form.save()
        messages.success(self.request, form.get_success_message())
        if self.request.is_ajax():
            return JsonResponse(form.data)
        return super(AccountSettingsView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = {'view': self, 'action': self.action}
        if self.action:
            context['form'] = self.get_form()
        context.update(kwargs)
        return context

    def get_form_class(self):
        return getattr(account_forms, 'Account%sForm' % self.action.capitalize())

    def get_form_kwargs(self):
        kwargs = super(AccountSettingsView, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_success_url(self):
        return reverse('shopit-account-settings-%s' % self.action)

    def get_template_names(self):
        names = ['shopit/account/account_settings_%s.html' % self.action] if self.action else []
        names.append('shopit/account/account_settings.html')
        return names

    @property
    def allowed_methods(self):
        allowed = self._allowed_methods()
        if not self.action:
            allowed.remove('POST')
        return allowed
