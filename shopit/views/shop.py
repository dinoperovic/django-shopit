# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.generic import FormView, TemplateView
from shop.modifiers.pool import cart_modifiers_pool

from shopit.forms import shop as shop_forms
from shopit.models.cart import Cart, CartItem
from shopit.models.order import Order


class CartObjectMixin(object):
    """
    Cart object mixin adds cart, cart items and watch items to the context.
    Resets the values from `extra` dict that are populated by the checkout.
    """
    def dispatch(self, request, *args, **kwargs):
        self.cart = Cart.objects.get_or_create_from_request(request)
        for key in ['payment_modifier', 'shipping_modifier', 'annotation']:
            self.cart.extra.pop(key, None)
        self.update_cart()
        self.cart.save()
        return super(CartObjectMixin, self).dispatch(request, *args, **kwargs)

    def update_cart(self):
        self.cart._dirty = True
        self.cart._cached_cart_items = None
        self.cart.update(self.request)

    def get_cart_data(self):
        return {
            'cart': self.cart,
            'cart_items': self.cart._cached_cart_items,
            'watch_items': CartItem.objects.filter_watch_items(self.cart, self.request),
        }

    def get_context_data(self, **kwargs):
        context = super(CartObjectMixin, self).get_context_data(**kwargs)
        context.update(self.get_cart_data())
        return context


class CartView(CartObjectMixin, FormView):
    """
    Cart view displays the cart and handles updating item's quantity,
    deleting the cart and adding modifier codes to the cart.
    """
    empty = False
    form_class = shop_forms.CartDiscountCodeForm
    template_name = 'shopit/shop/cart.html'

    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        if self.empty:
            for cart_item in Cart.objects.get_from_request(request).items.all():
                cart_item.delete()
        return super(CartView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.save()
        return redirect('shopit-cart')

    def get_form_kwargs(self):
        kwargs = super(CartView, self).get_form_kwargs()
        kwargs['cart'] = self.cart
        return kwargs

    @method_decorator(csrf_protect)
    def post(self, request, *args, **kwargs):
        for item, quantity in [x for x in request.POST.items() if x[0].startswith('quantity') and x[1]]:
            item, quantity = int(item.split('-').pop()), int(quantity)
            item = CartItem.objects.get(pk=item)
            if quantity > 0:
                available, diff = item.product.is_available(quantity)
                if available:
                    item.quantity = quantity
                else:
                    item.quantity = quantity + diff
                item.save()
            else:
                item.delete()
        self.update_cart()
        return super(CartView, self).post(request, *args, **kwargs)


class WatchView(CartObjectMixin, TemplateView):
    template_name = 'shopit/shop/watch.html'


class CheckoutView(CartObjectMixin, FormView):
    """
    Checkout view that handles customer selection forms and redirects to
    purchase url of selected payment provider.
    """
    template_name = 'shopit/shop/checkout.html'

    def forms_valid(self, **forms):
        """
        All the forms are valid, make the purchase happen. Return's JSON.
        """
        forms['customer_form'].save()
        self.cart.shipping_address = forms['shipping_form'].save()
        self.cart.billing_address = forms['billing_form'].save()
        self.cart.extra.update(forms['payment_form'].cleaned_data)
        self.cart.extra.update(forms['delivery_form'].cleaned_data)
        self.cart.extra.update(forms['extra_form'].cleaned_data)
        self.update_cart()
        self.cart.save()
        for modifier in cart_modifiers_pool.get_payment_modifiers():
            if modifier.is_active(self.cart):
                payment_provider = getattr(modifier, 'payment_provider', None)
                if payment_provider:
                    expression = payment_provider.get_payment_request(self.cart, self.request)
                    return JsonResponse({'expression': expression})
        return HttpResponseBadRequest()

    def forms_invalid(self, **forms):
        self.cart.save()
        errors = dict([('%s-%s' % (x.prefix, y[0]), y[1]) for x in forms.values() for y in x.errors.items()])
        return JsonResponse(errors, status=400)

    @method_decorator(never_cache)
    def get(self, request, *args, **kwargs):
        response = super(CheckoutView, self).get(request, *args, **kwargs)
        return response if not self.cart.is_empty else redirect('shopit-cart')

    def get_context_data(self, **kwargs):
        context = {'view': self}
        context.update(self.get_cart_data())
        context.update(self.get_forms())
        context.update(kwargs)
        return context

    def get_forms(self, **kwargs):
        kwargs['request'] = self.request
        kwargs['cart'] = self.cart
        forms = {
            'shipping_form': shop_forms.ShippingAddressForm(prefix='shipping', **kwargs),
            'billing_form': shop_forms.BillingAddressForm(prefix='billing', **kwargs),
            'payment_form': shop_forms.PaymentMethodForm(prefix='payment', **kwargs),
            'delivery_form': shop_forms.DeliveryMethodForm(prefix='delivery', **kwargs),
            'extra_form': shop_forms.ExtraAnnotationForm(prefix='extra', **kwargs),
            'accept_form': shop_forms.AcceptConditionForm(prefix='accept', **kwargs),
        }
        if self.request.customer.is_registered():
            forms['customer_form'] = shop_forms.CustomerForm(prefix='customer', **kwargs)
        else:
            forms['customer_form'] = shop_forms.GuestForm(prefix='guest', **kwargs)
        return forms

    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def post(self, request, *args, **kwargs):
        """
        Ment to be accessed via ajax, since the `get_payment_request` method
        from the payment provider returns a javascript expression that needs
        to be evaluated within javascript.
        """
        if not request.is_ajax():
            return HttpResponseBadRequest()

        forms = self.get_forms(data=request.POST)
        if all([x.is_valid() for x in forms.values()]):
            return self.forms_valid(**forms)
        return self.forms_invalid(**forms)


class ThanksView(TemplateView):
    """
    A generic thank you view, adds last updated order to the context,
    redirects to cart if no order.
    """
    template_name = 'shopit/shop/thanks.html'

    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        self.order = Order.objects.filter_from_request(request).first()
        if not self.order:
            return redirect('shopit-cart')
        return super(ThanksView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ThanksView, self).get_context_data(**kwargs)
        context['order'] = self.order
        return context
