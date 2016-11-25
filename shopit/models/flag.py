# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from parler.managers import TranslatableQuerySet
from parler.models import TranslatableModel, TranslatedFields


class FlagQuerySet(TranslatableQuerySet):
    def active(self):
        return self.filter(active=True)


@python_2_unicode_compatible
class Flag(TranslatableModel):
    """
    Flag model.
    """
    translations = TranslatedFields(
        name=models.CharField(_('Name'), max_length=128),
    )

    code = models.SlugField(_('Code'), unique=True, help_text=_('Unique identifier for this flag.'))

    active = models.BooleanField(_('Active'), default=True, help_text=_('Is this flag publicly visible.'))
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)
    order = models.PositiveIntegerField(_('Sort'), default=0)

    objects = FlagQuerySet.as_manager()

    class Meta:
        db_table = 'shopit_flags'
        verbose_name = _('Flag')
        verbose_name_plural = _('Flags')
        ordering = ['order']

    def __str__(self):
        return self.safe_translation_getter('name', any_language=True)

    def get_products(self):
        """
        Returs all flagged products with this flag.
        """
        products = getattr(self, '_products', None)
        if products is None:
            products = self.product_set.active()
            for model in ['category', 'brand', 'manufacturer']:
                for cat in getattr(self, '%s_set' % model).active():
                    products = products | cat.get_products()
            setattr(self, '_products', products.distinct())
        return products
