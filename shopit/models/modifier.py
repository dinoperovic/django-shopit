# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, Count
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from parler.managers import TranslatableQuerySet
from parler.models import TranslatableModel, TranslatedFields
from shop.money import Money
from shop.money.fields import MoneyField

from shopit.models.cart import CartDiscountCode
from shopit.models.customer import Customer
from shopit.modifier_conditions import modifier_conditions_pool
from shopit.settings import ERROR_MESSAGES as EM


class ModifierQuerySet(TranslatableQuerySet):
    def active(self):
        return self.filter(active=True)

    def filtering_enabled(self):
        return self.filter(kind__in=[Modifier.STANDARD, Modifier.DISCOUNT]).\
            prefetch_related('discount_codes').prefetch_related('conditions').\
            annotate(num_discount_codes=Count('discount_codes'), num_conditions=Count('conditions')).\
            filter(num_discount_codes=0, num_conditions=0)


@python_2_unicode_compatible
class Modifier(TranslatableModel):
    STANDARD = 'standard'
    DISCOUNT = 'discount'
    CART = 'cart'

    KINDS = (
        (STANDARD, _('Standard')),
        (DISCOUNT, _('Discount')),
        (CART, _('Cart')),
    )

    translations = TranslatedFields(
        name=models.CharField(_('Name'), max_length=128),
    )

    code = models.SlugField(_('Code'), unique=True, help_text=_('Unique identifier for this modifier.'))

    amount = MoneyField(_('Amount'), default=Money(0), help_text=('Amount that should be added. Can be negative.'))

    percent = models.DecimalField(
        _('Percent'), blank=True, null=True, max_digits=4, decimal_places=2,
        help_text=_('Percent that should be added, overrides the amount. Can be negative.'))

    kind = models.CharField(_('Kind'), max_length=16, choices=KINDS, default=STANDARD, help_text=_(
        'Standard affects the product regardles, Discount checks for a "Discountable" flag on a product and should be '
        'negative, Cart will affect an entire cart.'))

    active = models.BooleanField(_('Active'), default=True, help_text=_('Is this modifier publicly visible.'))
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)
    order = models.PositiveIntegerField(_('Sort'), default=0)

    objects = ModifierQuerySet.as_manager()

    class Meta:
        db_table = 'shopit_modifiers'
        verbose_name = _('Modifier')
        verbose_name_plural = _('Modifiers')
        ordering = ['order']

    def __str__(self):
        return self.label

    def save(self, *args, **kwargs):
        self.clean()
        super(Modifier, self).save(*args, **kwargs)

    @property
    def label(self):
        return self.safe_translation_getter('name', any_language=True)

    @property
    def requires_code(self):
        return self.discount_codes.active().exists()

    @property
    def is_filtering_enabled(self):
        return Modifier.objects.filtering_enabled().active().filter(id=self.id).exists()

    def get_conditions(self):
        if not hasattr(self, '_conditions'):
            setattr(self, '_conditions', self.conditions.all())
        return getattr(self, '_conditions')

    def get_discount_codes(self):
        if not hasattr(self, '_discount_codes'):
            setattr(self, '_discount_codes', self.discount_codes.valid())
        return getattr(self, '_discount_codes')

    def get_added_amount(self, price, quantity=1):
        return self.percent * price / 100 if self.percent else self.amount * quantity

    def can_be_applied(self, request, cart_item=None, cart=None):
        """
        Returns if a modifier can be applied to the given cart or cart item.
        Either `cart_item` or `cart` must be passed in.
        """
        if cart_item is None and cart is None:
            return False

        if cart_item and not self.is_eligible_product(cart_item.product):
            return False

        for condition in self.get_conditions():
            if not condition.is_met(request, cart_item, cart):
                return False

        if self.requires_code and not self.is_code_applied(cart_item.cart_id if cart_item else cart.id):
            return False

        return self.active  # Should never happen to be False up to this point, but just in case.

    def is_eligible_product(self, product):
        """
        Returns if modifier can be applied to the given product.
        """
        if self.kind == self.DISCOUNT:
            return product.discountable
        return self.kind == self.STANDARD

    def is_code_applied(self, cart_id):
        """
        Make sure that at least one code is applied to the given cart.
        """
        cart_codes = CartDiscountCode.objects.filter(cart_id=cart_id).values_list('code', flat=True)
        for code in self.get_discount_codes():
            if code.code in cart_codes:
                return True
        return False

    def clean(self):
        if self.kind == self.DISCOUNT:
            if self.percent and self.percent >= 0 or not self.percent and self.amount >= 0:
                raise ValidationError(EM['discount_not_negative'])

    @classmethod
    def get_cart_modifiers(cls):
        return cls.objects.filter(kind=cls.CART)


@python_2_unicode_compatible
class ModifierCondition(models.Model):
    """
    Inline model for Modifier that adds conditions that must be met for
    Modifier to be valid.
    """
    CONDITIONS = modifier_conditions_pool.get_condition_choices()

    modifier = models.ForeignKey(Modifier, models.CASCADE, related_name='conditions', verbose_name=_('Modifier'))
    path = models.CharField(_('Condition'), max_length=255, blank=True, choices=CONDITIONS)
    value = models.DecimalField(_('Value'), blank=True, null=True, max_digits=10, decimal_places=2)

    order = models.PositiveIntegerField(_('Sort'), default=0)

    class Meta:
        db_table = 'shopit_modifier_conditions'
        verbose_name = _('Condition')
        verbose_name_plural = _('Conditions')
        ordering = ['order']

    def __str__(self):
        name = dict(self.CONDITIONS).get(self.path)
        name = '%s %s' % (name, self.value or '')
        return name.rstrip()

    def save(self, *args, **kwargs):
        self.clean()
        super(ModifierCondition, self).save(*args, **kwargs)

    def is_met(self, request, cart_item=None, cart=None):
        if self.condition and cart_item:
            return self.condition.cart_item_condition(request, cart_item, self.value)
        if self.condition and cart:
            return self.condition.cart_condition(request, cart, self.value)
        return True

    def clean(self):
        if not self.path:
            raise ValidationError(EM['modifier_no_condition_path'])

    @cached_property
    def condition(self):
        return modifier_conditions_pool.get_condition(self.path)


class DiscountCodeQuerySet(models.QuerySet):
    def active(self):
        return self.filter(active=True)

    def valid(self):
        now = timezone.now()
        return self.active().filter(Q(valid_from__lte=now) & (Q(valid_until__isnull=True) | Q(valid_until__gt=now)))


@python_2_unicode_compatible
class DiscountCode(models.Model):
    """
    Discount code model when added to the modifier, it requires it to also
    be added to the cart.
    """
    modifier = models.ForeignKey(
        Modifier, models.CASCADE, related_name='discount_codes', verbose_name=_('Modifier'),
        help_text=_('Modifier that this discount code applies to.'))

    code = models.CharField(_('Code'), max_length=30, unique=True, help_text=_(
        'Code that must be entered for the modifier to activate.'))

    customer = models.ForeignKey(
        Customer, models.CASCADE, blank=True, null=True, related_name='discount_codes', verbose_name=_('Customer'),
        help_text=_('Limit code so that it can be used only by a specific customer.'))

    active = models.BooleanField(_('Active'), default=True)
    valid_from = models.DateTimeField(_('Valid from'), default=timezone.now)
    valid_until = models.DateTimeField(_('Valid until'), blank=True, null=True)
    order = models.PositiveIntegerField(_('Sort'), default=0)

    objects = DiscountCodeQuerySet.as_manager()

    class Meta:
        db_table = 'shopit_discount_codes'
        verbose_name = _('Discount code')
        verbose_name_plural = _('Discount codes')
        ordering = ['order']

    def __str__(self):
        return self.code

    @property
    def is_valid(self):
        now = timezone.now()
        if self.valid_until:
            return self.active and self.valid_from <= now and self.valid_until > now
        return self.active and self.valid_from <= now
