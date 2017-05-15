# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import models
from django.db.models import Q
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from mptt.managers import TreeManager
from mptt.models import MPTTModel, TreeForeignKey
from mptt.querysets import TreeQuerySet
from parler.managers import TranslatableManager, TranslatableQuerySet
from parler.models import TranslatableModelMixin, TranslatedFields


class FlagQuerySet(TranslatableQuerySet, TreeQuerySet):
    def active(self):
        return self.filter(Q(active=True) & (Q(parent__isnull=True) | Q(parent__active=True)))


class FlagManager(TranslatableManager, TreeManager):
    queryset_class = FlagQuerySet

    def get_queryset(self):
        return self.queryset_class(self.model, using=self._db).order_by('tree_id', 'lft')

    def active(self):
        return self.get_queryset().active()


@python_2_unicode_compatible
class Flag(TranslatableModelMixin, MPTTModel):
    """
    Flag model.
    """
    translations = TranslatedFields(
        name=models.CharField(_('Name'), max_length=128),
    )

    code = models.SlugField(_('Code'), unique=True, help_text=_('Unique identifier for this flag.'))

    parent = TreeForeignKey(
        'self', models.CASCADE, blank=True, null=True, related_name='children', verbose_name=_('Parent'))

    active = models.BooleanField(_('Active'), default=True, help_text=_('Is this flag publicly visible.'))
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)

    objects = FlagManager()

    class Meta:
        db_table = 'shopit_flags'
        verbose_name = _('Flag')
        verbose_name_plural = _('Flags')
        ordering = ['tree_id', 'lft']

    def __str__(self):
        name = self.safe_translation_getter('name', any_language=True)
        return '%s | %s' % (str(self.parent), name) if self.parent else name

    def get_products(self):
        """
        Returs all flagged products with this flag.
        """
        products = getattr(self, '_products', None)
        if products is None:
            products = self.product_set.active()
            setattr(self, '_products', products)
        return products
