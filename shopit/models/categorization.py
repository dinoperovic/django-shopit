# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from cms.models.fields import PlaceholderField
from cms.utils.i18n import get_current_language
from django.core.urlresolvers import NoReverseMatch, reverse
from django.db import models
from django.db.models import Q
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from filer.fields.image import FilerImageField
from mptt.managers import TreeManager
from mptt.models import MPTTModel, TreeForeignKey
from mptt.querysets import TreeQuerySet
from parler.managers import TranslatableManager, TranslatableQuerySet
from parler.models import TranslatableModelMixin, TranslatedFields
from parler.utils.context import switch_language

from shopit.models.flag import Flag
from shopit.models.modifier import Modifier
from shopit.models.tax import Tax


class CategorizationQuerySet(TranslatableQuerySet, TreeQuerySet):
    def active(self):
        return self.filter(Q(active=True) & (Q(parent__isnull=True) | Q(parent__active=True)))


class CategorizationManager(TranslatableManager, TreeManager):
    queryset_class = CategorizationQuerySet

    def get_queryset(self):
        return self.queryset_class(self.model, using=self._db).order_by('tree_id', 'lft')

    def active(self):
        return self.get_queryset().active()


def _categorization_translated_fields():
    return TranslatedFields(
        name=models.CharField(
            _('Name'),
            max_length=128,
        ),
        slug=models.SlugField(
            _('Slug'),
            db_index=True,
        ),
        description=models.TextField(
            _('Description'),
            blank=True,
            help_text=_("Description of a categorization, usually used as lead text in categorization's detail view."),
        ),
        meta={
            'unique_together': [('language_code', 'slug')],
        },
    )


@python_2_unicode_compatible
class CategorizationModel(TranslatableModelMixin, MPTTModel):
    """
    Categorization model, adds translated fields and uses django-mptt.
    Intended for use like this:
        class Category(CategorizationModel):
            translations = _categorization_translated_fields()
    """
    _featured_image = FilerImageField(
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('Featured image'),
        help_text=_("If left empty for childs, a parent's featured image will be used."),
    )

    parent = TreeForeignKey(
        'self',
        models.CASCADE,
        blank=True,
        null=True,
        related_name='children',
        verbose_name=_('Parent'),
    )

    modifiers = models.ManyToManyField(
        Modifier,
        blank=True,
        verbose_name=_('Modifiers'),
        limit_choices_to={'kind__in': [Modifier.STANDARD, Modifier.DISCOUNT]},
    )

    flags = models.ManyToManyField(
        Flag,
        blank=True,
        verbose_name=_('Flags'),
        help_text=_('Check flags for products in this categorization.'),
    )

    active = models.BooleanField(
        _('Active'),
        default=True,
        help_text=_('Is this categorization publicly visible.'),
    )

    created_at = models.DateTimeField(
        _('Created at'),
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        _('Updated at'),
        auto_now=True,
    )

    objects = CategorizationManager()

    class Meta:
        abstract = True

    def __str__(self):
        return self.safe_translation_getter('name', any_language=True)

    def get_absolute_url(self, language=None):
        if not language:
            language = get_current_language()

        url_name = 'shopit-%s-detail' % self._meta.model.__name__.lower()

        with switch_language(self, language):
            try:
                return reverse(url_name, args=[self.get_path()])
            except NoReverseMatch:
                pass

    def get_path(self):
        """
        Returns ful url path for categorization object.
        """
        path = []
        for obj in self.get_ancestors(include_self=True):
            path.append(obj.safe_translation_getter('slug', ''))
        return '/'.join(path)

    @property
    def featured_image(self):
        if not self._featured_image and self.is_child_node():
            return self.parent.featured_image
        return self._featured_image

    @featured_image.setter
    def featured_image(self, value):
        self._featured_image = value

    def get_products(self):
        """
        Returns active products from this categorization
        """
        products = getattr(self, '_products', None)
        if products is None:
            products = self.product_set.active()
            for child in self.get_descendants():
                products = products | child.product_set.active()
            setattr(self, '_products', products)
        return products

    def get_modifiers(self, distinct=True):
        """
        Returns all modifiers for the current tree.
        """
        mods = getattr(self, '_mods', None)
        if mods is None:
            mods = self.modifiers.active()
            for parent in self.get_ancestors():
                mods = mods | parent.modifiers.active()
            setattr(self, '_mods', mods)
        return mods.distinct() if distinct else mods

    def get_flags(self, distinct=True):
        """
        Returns all flags for the current tree.
        """
        flags = getattr(self, '_flags', None)
        if flags is None:
            flags = self.flags.active()
            for parent in self.get_ancestors():
                flags = flags | parent.flags.active()
            setattr(self, '_flags', flags)
        return flags.distinct() if distinct else flags


class Category(CategorizationModel):
    translations = _categorization_translated_fields()

    content = PlaceholderField('shopit_category_content')

    _tax = models.ForeignKey(
        Tax,
        models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('Tax'),
        help_text=_("Tax to be applied to products in this category. If empty, parent's tax will be used."),
    )

    class Meta:
        db_table = 'shopit_categories'
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')
        ordering = ['tree_id', 'lft']

    @property
    def tax(self):
        if not self._tax and self.parent:
            return self.parent.tax
        return self._tax

    @tax.setter
    def tax(self, value):
        self._tax = value


class Brand(CategorizationModel):
    translations = _categorization_translated_fields()

    content = PlaceholderField('shopit_brand_content')

    class Meta:
        db_table = 'shopit_brands'
        verbose_name = _('Brand')
        verbose_name_plural = _('Brands')
        ordering = ['tree_id', 'lft']


class Manufacturer(CategorizationModel):
    translations = _categorization_translated_fields()

    content = PlaceholderField('shopit_manufacturer_content')

    class Meta:
        db_table = 'shopit_manufacturers'
        verbose_name = _('Manufacturer')
        verbose_name_plural = _('Manufacturers')
        ordering = ['tree_id', 'lft']
