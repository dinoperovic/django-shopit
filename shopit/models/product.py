# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import itertools
from collections import OrderedDict
from datetime import datetime
from decimal import Decimal
from os.path import basename

from cms.models.fields import PlaceholderField
from cms.utils.i18n import get_current_language
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.urlresolvers import NoReverseMatch, reverse
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import Count
from django.db.models.query import QuerySet
from django.template.defaultfilters import truncatewords
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.encoding import python_2_unicode_compatible
from django.utils.functional import cached_property
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from django_measurement.models import MeasurementField
from easy_thumbnails.exceptions import InvalidImageFormatError
from filer.fields.file import FilerFileField
from measurement.measures import Distance, Mass
from mptt.fields import TreeForeignKey
from parler.managers import TranslatableManager, TranslatableQuerySet
from parler.models import TranslatableModel, TranslatedFields
from parler.utils.context import switch_language
from polymorphic.query import PolymorphicQuerySet
from shop.models.product import BaseProduct, BaseProductManager
from shop.money.fields import MoneyField

from shopit.models.cart import Cart
from shopit.models.categorization import Brand, Category, Manufacturer
from shopit.models.customer import Customer
from shopit.models.flag import Flag
from shopit.models.modifier import Modifier
from shopit.models.tax import Tax
from shopit.settings import ERROR_MESSAGES as EM
from shopit.settings import ATTRIBUTE_TEMPLATES, FILTER_ATTRIBUTES_INCLUDES_VARIANTS, RELATION_KINDS, REVIEW_RATINGS

try:
    from easy_thumbnails.files import get_thumbnailer
    from easy_thumbnails.alias import aliases
    EASY_THUMBNAILS = True
except ImportError:  # pragma: no cover
    EASY_THUMBNAILS = False


class ProductQuerySet(PolymorphicQuerySet, TranslatableQuerySet):
    def active(self):
        return self.filter(active=True)

    def top_level(self):
        return self.filter(kind__in=[Product.SINGLE, Product.GROUP])

    def filter_categorization(self, categories=None, brands=None, manufacturers=None):
        """
        Filters a queryset by the given categorization. A list of slugs should
        be passed in.
        """
        filters = {}
        if categories:
            ids = Category.objects.translated(slug__in=categories).values_list('id', flat=True)
            filters['_category_id__in'] = list(set(ids))
        if brands:
            ids = Brand.objects.translated(slug__in=brands).values_list('id', flat=True)
            filters['_brand_id__in'] = list(set(ids))
        if manufacturers:
            ids = Manufacturer.objects.translated(slug__in=manufacturers).values_list('id', flat=True)
            filters['_manufacturer_id__in'] = list(set(ids))
        return self.filter(**filters) if filters else self

    def filter_flags(self, flags=None):
        """
        Filters a queryset by the given flags. A list of codes should be
        passed in.
        """
        filters = {}
        if flags:
            flagged = self.prefetch_related('flags').filter(flags__code__in=flags)
            flagged = flagged.annotate(num_flags=Count('flags')).filter(num_flags=len(flags)).distinct()
            filters['id__in'] = flagged.values_list('id', flat=True)
        return self.filter(**filters) if filters else self

    def filter_modifiers(self, modifiers=None):
        """
        Filters a queryset by the given modifiers. A list of codes should be
        passed in.
        """
        filters = {}
        if modifiers:
            enabled = Modifier.objects.filtering_enabled().active().values_list('code', flat=True)
            if len([x for x in modifiers if x in enabled]) < len(modifiers):
                # Return empty queryset if invalid modifiers are passed in.
                return self.none()

            modded = self.prefetch_related('modifiers').filter(modifiers__code__in=modifiers)
            modded = modded.annotate(num_mods=Count('modifiers')).filter(num_mods=len(modifiers)).distinct()
            filters['id__in'] = modded.values_list('id', flat=True)
        return self.filter(**filters) if filters else self

    def filter_attributes(self, attributes=None):
        """
        Filters a queryset by attributes. A list of tuples containing attribute
        code, name should be passed in as `attributes`.
        """
        if attributes:
            ids = self.values_list('id', flat=True)
            variants = Product.objects.filter(group_id__in=ids).\
                prefetch_related('attribute_values', 'attribute_values__attribute', 'attribute_values__choice')

            if variants:
                for code, value in attributes:
                    filters = {'attribute_values__attribute__code__iexact': code}
                    if value:
                        filters['attribute_values__choice__value__iexact'] = value
                    else:
                        filters['attribute_values__choice__isnull'] = True
                    variants = variants.filter(**filters)

                group_ids = list(set(variants.values_list('group_id', flat=True)))
                self = self.filter(id__in=group_ids)

                if FILTER_ATTRIBUTES_INCLUDES_VARIANTS:
                    self = (self | variants).order_by('-order', 'kind', 'published')
        return self

    def filter_price(self, price_from=None, price_to=None):
        """
        Filters a queryset by a price range.
        """
        filters = {}
        if price_from:
            filters['_unit_price__gte'] = Decimal(price_from)
        if price_to:
            filters['_unit_price__lte'] = Decimal(price_to)
        return self.filter(**filters) if filters else self


class ProductManager(BaseProductManager, TranslatableManager):
    queryset_class = ProductQuerySet

    def active(self):
        return self.get_queryset().active()

    def top_level(self):
        return self.get_queryset().top_level()

    def filter_categorization(self, categories=None, brands=None, manufacturers=None):
        return self.get_queryset().filter_categorization(categories, brands, manufacturers)

    def filter_flags(self, flags=None):
        return self.get_queryset().filter_flags(flags)

    def filter_modifiers(self, modifiers=None):
        return self.get_queryset().filter_modifiers(modifiers)

    def filter_price(self, price_from=None, price_to=None):
        return self.get_queryset().filter_price(price_from, price_to)

    def filter_attributes(self, attributes=None):
        return self.get_queryset().filter_attributes(attributes)


@python_2_unicode_compatible
class Product(BaseProduct, TranslatableModel):
    """
    Product model.
    """
    SINGLE, GROUP, VARIANT = range(3)

    KINDS = (
        (SINGLE, _('Single')),
        (GROUP, _('Group')),
        (VARIANT, _('Variant')),
    )

    translations = TranslatedFields(
        name=models.CharField(_('Name'), max_length=128),
        slug=models.SlugField(_('Slug'), db_index=True, help_text=_(
            "Part that's used in url to display this product. Needs to be unique.")),
        _caption=models.TextField(_('Caption'), max_length=255, blank=True, help_text=_(
            "Short product caption, usually used in catalog's list view of products.")),
        _description=models.TextField(_('Description'), blank=True, help_text=_(
            "Description of a product, usually used as lead text in product's detail view.")),
        meta={'unique_together': [('language_code', 'slug')]},
    )

    code = models.CharField(_('Code'), max_length=64, unique=True, help_text=_('Unique identifier for a product.'))

    # Categorization
    _category = TreeForeignKey(Category, models.CASCADE, blank=True, null=True, verbose_name=_('Category'))
    _brand = TreeForeignKey(Brand, models.CASCADE, blank=True, null=True, verbose_name=_('Brand'))
    _manufacturer = TreeForeignKey(Manufacturer, models.CASCADE, blank=True, null=True, verbose_name=_('Manufacturer'))

    # Pricing
    _unit_price = MoneyField(_('Unit price'), blank=True, null=True, help_text=_(
        "For variants leave empty to use the Group price."))

    _discount = models.DecimalField(
        _('Discount %'), blank=True, null=True, max_digits=4, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_("For variants leave empty to use Group discount."))

    _tax = models.ForeignKey(
        Tax, models.SET_NULL, blank=True, null=True, verbose_name=_('Tax'),
        help_text=_("Tax to be applied to this product. Variants inherit tax percentage from their Group, and should "
                    "leave this field empty."))

    # Settings
    kind = models.PositiveSmallIntegerField(_('Kind'), choices=KINDS, default=SINGLE, help_text=_(
        'Choose a product type. Single products are products without variations. Group products are base products '
        'that hold variants and their common info, they cannot be added to cart. Variants are variations of a product '
        'that must select a Group product, and set their unique set of attributes. '
        '(See "Variant" section below)'))

    discountable = models.BooleanField(_('Discountable'), default=True, help_text=_(
        'Can this product be used in an offer?'))

    modifiers = models.ManyToManyField(
        Modifier, blank=True, verbose_name=_('Modifiers'),
        limit_choices_to={'kind__in': [Modifier.STANDARD, Modifier.DISCOUNT]})

    flags = models.ManyToManyField(Flag, blank=True, verbose_name=_('Flags'), help_text=_(
        'Check flags for this product.'))

    # Measurements
    _width = MeasurementField(_('Width'), blank=True, null=True, measurement=Distance)
    _height = MeasurementField(_('Height'), blank=True, null=True, measurement=Distance)
    _depth = MeasurementField(_('Depth'), blank=True, null=True, measurement=Distance)
    _weight = MeasurementField(_('Weight'), blank=True, null=True, measurement=Mass)

    # Group
    available_attributes = models.ManyToManyField(
        'Attribute', blank=True, related_name='products_available_attributes', verbose_name=_('Attributes'),
        help_text=_('Select attributes that can be used in a Variant for this product.'))

    # Variant
    group = models.ForeignKey(
        'self', models.CASCADE, blank=True, null=True, related_name='variants', verbose_name=_('Group'),
        help_text=_('Select a Group product for this variation.'))

    attributes = models.ManyToManyField('Attribute', through='AttributeValue', verbose_name=_('Attributes'))
    published = models.DateTimeField(_('Published'), default=timezone.now)

    quantity = models.IntegerField(_('Quantity'), blank=True, null=True, help_text=_(
        'Number of available products to ship. Leave empty if product is always available, or set to 0 if product '
        'is not available.'))

    order = models.BigIntegerField(_('Sort'), default=0)

    content = PlaceholderField('shopit_product_content')

    objects = ProductManager()
    lookup_fields = ['code__startswith', 'translations__name__icontains']

    class Meta:
        db_table = 'shopit_products'
        verbose_name = _('Product')
        verbose_name_plural = _('Products')
        ordering = ['-order']

    def __str__(self):
        return self.product_name

    def get_absolute_url(self, language=None):
        if not language:
            language = get_current_language()

        with switch_language(self, language):
            try:
                return reverse('shopit-product-detail', args=[self.safe_translation_getter('slug')])
            except NoReverseMatch:  # pragma: no cover
                pass

    def save(self, *args, **kwargs):
        """
        Clean and clear product.
        Set unique ordering value for product and it's variants based on
        published timestamp. Force Single groups to a Group kind.
        """
        self.clean()
        self.clear()
        if self.is_variant:
            self.group.clear('_variants', '_invalid_variants', '_variations', '_attribute_choices', '_combinations')
            self.order = self.group.order
            if self.group.is_single:
                self.group.kind = Product.GROUP
                self.group.save(update_fields=['kind'])
            super(Product, self).save(*args, **kwargs)
        else:
            # Don't generate timestamp if published hasn't changed.
            if self.pk is not None:
                original = Product.objects.get(pk=self.pk).published.strftime('%s')
                if original == self.published.strftime('%s'):
                    super(Product, self).save(*args, **kwargs)
                    return
            timestamp = int(self.published.strftime('%s'))
            same = Product.objects.filter(order__startswith=timestamp).first()
            timestamp = same.order + 1 if same else timestamp * 1000
            self.order = timestamp
            super(Product, self).save(*args, **kwargs)
            if self.is_group:
                for variant in self.get_variants():
                    variant.clear()
                    variant.order = timestamp
                    variant.save(update_fields=['order'])

    @property
    def product_name(self):
        return self.safe_translation_getter('name', any_language=True) if self.pk else ''

    @property
    def product_code(self):
        return self.code

    @property
    def is_single(self):
        return self.kind == self.SINGLE

    @property
    def is_group(self):
        return self.kind == self.GROUP

    @property
    def is_variant(self):
        return self.kind == self.VARIANT

    @property
    def caption(self):
        return self.get_attr('_caption', '', translated=True)

    @caption.setter
    def caption(self, value):
        self._caption = value

    @property
    def description(self):
        return self.get_attr('_description', '', translated=True)

    @description.setter
    def description(self, value):
        self._description = value

    @property
    def category(self):
        return self.get_attr('_category')

    @category.setter
    def category(self, value):
        self._category = value

    @property
    def brand(self):
        return self.get_attr('_brand')

    @brand.setter
    def brand(self, value):
        self._brand = value

    @property
    def manufacturer(self):
        return self.get_attr('_manufacturer')

    @manufacturer.setter
    def manufacturer(self, value):
        self._manufacturer = value

    @property
    def unit_price(self):
        return self.get_attr('_unit_price', 0)

    @unit_price.setter
    def unit_price(self, value):
        self._unit_price = value

    @property
    def discount(self):
        return self.get_attr('_discount')

    @discount.setter
    def discount(self, value):
        self._discount = value

    @property
    def tax(self):
        return self.get_attr('_tax') or getattr(self.category, 'tax', None)

    @tax.setter
    def tax(self, value):
        self._tax = value

    @property
    def width(self):
        return self.get_attr('_width')

    @width.setter
    def width(self, value):
        self._width = value if isinstance(value, Distance) else Distance(m=value)

    @property
    def height(self):
        return self.get_attr('_height')

    @height.setter
    def height(self, value):
        self._height = value if isinstance(value, Distance) else Distance(m=value)

    @property
    def depth(self):
        return self.get_attr('_depth')

    @depth.setter
    def depth(self, value):
        self._depth = value if isinstance(value, Distance) else Distance(m=value)

    @property
    def weight(self):
        return self.get_attr('_weight')

    @weight.setter
    def weight(self, value):
        self._weight = value if isinstance(value, Mass) else Mass(g=value)

    @property
    def price(self):
        return self.get_price()

    @property
    def is_discounted(self):
        return bool(self.discount_percent)

    @property
    def is_taxed(self):
        return bool(self.tax_percent)

    @property
    def discount_percent(self):
        return self.discount or Decimal('0.00')

    @property
    def tax_percent(self):
        return getattr(self.tax, 'percent', Decimal('0.00'))

    @property
    def discount_amount(self):
        return self.unit_price * self.discount_percent / 100

    @property
    def tax_amount(self):
        return (self.unit_price - self.discount_amount) * self.tax_percent / 100

    @property
    def primary_image(self):
        return self.images.first()

    @cached_property
    def images(self):
        images = self.attachments.filter(kind=Attachment.IMAGE)
        return images or (self.group.images if self.is_variant else images)

    @cached_property
    def videos(self):
        videos = self.attachments.filter(kind=Attachment.VIDEO)
        return videos or (self.group.videos if self.is_variant else videos)

    @cached_property
    def files(self):
        files = self.attachments.filter(kind=Attachment.FILE)
        return files or (self.group.files if self.is_variant else files)

    def get_price(self, request=None):
        """
        Returns price with discount and tax calculated.
        """
        return self.unit_price - self.discount_amount + self.tax_amount

    def get_availability(self, request=None):
        """
        Returns product availibility as list of tuples `(quantity, until)`
        Method is not yet implemented in django-shop.
        """
        availability = self.quantity if self.quantity is not None else True
        if self.is_group:
            availability = 0
        elif self.is_variant and self not in self.group.get_variants():
            availability = 0
        return [(availability, datetime.max)]

    def is_available(self, quantity=1, request=None):
        """
        Returns if product is available for the given quantity. If request
        is passed in, count items already in cart.
        """
        if request:
            cart = Cart.objects.get_or_create_from_request(request)
            cart_item = self.is_in_cart(cart)
            quantity += cart_item.quantity if cart_item else 0

        now = timezone.now().replace(tzinfo=None)
        number, until = self.get_availability(request)[0]
        number = 100000 if number is True else number
        available = number >= quantity and now < until
        return available, int(number - quantity)

    def get_modifiers(self, distinct=True):
        """
        Returns all modifiers for this product.
        Collects categorization and group modifiers.
        """
        mods = getattr(self, '_mods', None)
        if mods is None:
            mods = self.modifiers.active()
            if self.is_variant:
                mods = mods | self.group.get_modifiers(distinct=False)
            else:
                if self.category:
                    mods = mods | self.category.get_modifiers(distinct=False)
                if self.brand:
                    mods = mods | self.brand.get_modifiers(distinct=False)
                if self.manufacturer:
                    mods = mods | self.manufacturer.get_modifiers(distinct=False)
            self.cache('_mods', mods)
        return mods.distinct() if distinct else mods

    def get_flags(self, distinct=True):
        """
        Returns all flags for this product.
        Collects categorization and group flags.
        """
        flags = getattr(self, '_flags', None)
        if flags is None:
            flags = self.flags.active()
            if self.is_variant:
                flags = flags | self.group.get_flags(distinct=False)
            self.cache('_flags', flags)
        return flags.distinct() if distinct else flags

    def get_available_attributes(self):
        """
        Returns list of available attributes for Group and
        Variant products.
        """
        if self.is_group:
            if not hasattr(self, '_available_attributes'):
                self.cache('_available_attributes', self.available_attributes.active())
            return getattr(self, '_available_attributes')

    def get_attributes(self):
        """
        Returns a dictionary containing Variant attributes.
        """
        if self.is_variant:
            attrs = getattr(self, '_attributes', OrderedDict())
            if not attrs:
                for value in self.attribute_values.select_related('attribute'):
                    attrs[value.attribute.key] = value.as_dict
                self.cache('_attributes', attrs)
            return attrs

    def get_variants(self):
        """
        Returns valid variants of a Group product.
        """
        if self.is_group:
            variants = getattr(self, '_variants', None)
            if variants is None:
                variants = self.variants.all()
                invalid = [x.pk for x in self.get_invalid_variants()]
                variants = self.variants.exclude(pk__in=invalid)
                self.cache('_variants', variants)
            return variants

    def get_invalid_variants(self):
        """
        Returns variants that whose attributes don't match available
        attributes and they need to be re-configured or deleted.
        """
        if self.is_group:
            if not hasattr(self, '_invalid_variants'):
                invalid = []
                valid_attrs = []  # Keep track of valid attrs to check for duplicates.
                codes = sorted(self.get_available_attributes().values_list('code', flat=True))
                for variant in self.variants.all():
                    attrs = variant.get_attributes()
                    if (attrs in valid_attrs or sorted(x['code'] for x in attrs.values()) != codes or
                            True in [not x['nullable'] and x['value'] == '' for x in attrs.values()]):
                        invalid.append(variant)
                    else:
                        valid_attrs.append(attrs)
                self.cache('_invalid_variants', invalid)
            return getattr(self, '_invalid_variants')

    def get_variations(self):
        """
        Returns a list of tuples containing a variant id and it's attributes.
        """
        if self.is_group:
            if not hasattr(self, '_variations'):
                variations = [(x.pk, x.get_attributes()) for x in self.get_variants()]
                self.cache('_variations', variations)
            return getattr(self, '_variations')

    def get_attribute_choices(self):
        """
        Returns available attribute choices for a group product, filtering
        only the used ones. Used to display dropdown fields on a group
        product to select a variant.
        """
        if self.is_group:
            if not hasattr(self, '_attribute_choices'):
                used = [tuple([y['code'], y['value']]) for x in self.get_variations() for y in x[1].values()]
                attrs = OrderedDict()
                for attr in self.get_available_attributes():
                    data = attr.as_dict
                    data['choices'] = [x for x in attr.get_choices() if (x.attribute.code, x.value) in used]
                    if data['choices']:
                        attrs[attr.code] = data
                self.cache('_attribute_choices', attrs)
            return getattr(self, '_attribute_choices')

    def get_combinations(self):
        """
        Returns all available Variant combinations for a Group product
        based on `Available attributes` field, replacing the existant
        variants with actual variant data. Variants with attributes
        missing or not specified in `Available attributes` will not be
        included. This is used to show possible combinations in admin,
        as well as creating them automatically.
        """
        if self.is_group:
            if not hasattr(self, '_combinations'):
                values = []
                for attr in self.get_available_attributes():
                    vals = [AttributeValue(attribute=attr, choice=x) for x in attr.get_choices()]
                    if vals:
                        values.append(vals)
                combinations = []
                if values:
                    for combo in itertools.product(*values):
                        attrs = OrderedDict([(x.attribute.code, x.value) for x in combo])
                        name = self.safe_translation_getter('name', any_language=True)
                        name = '%s %s' % (name, ' '.join([x.label for x in combo if x.label != '-']))
                        name = name.rstrip()
                        slug = slugify(name)
                        languages = []
                        variant = self.get_variant(attrs)
                        if variant:
                            name = variant.safe_translation_getter('name', name)
                            slug = variant.safe_translation_getter('slug', slug)
                            languages = variant.get_available_languages()
                        combinations.append({
                            'pk': variant.pk if variant else None,
                            'name': name,
                            'slug': slug,
                            'code': variant.code if variant else None,
                            'price': variant.get_price() if variant else None,
                            'quantity': variant.quantity if variant else None,
                            'languages': languages,
                            'attributes': OrderedDict([(x.attribute.code, x.as_dict) for x in combo])
                        })
                self.cache('_combinations', combinations)
            return getattr(self, '_combinations')

    def get_attachments(self):
        """
        Returns all attachments as a dictionary.
        If Product is a Variant and has not attachments itself,
        group attachemts are inherited.
        """
        attachments = getattr(self, '_attachments', None)
        if attachments is None:
            attachments = {
                'images': [x.as_dict for x in self.images] or None,
                'videos': [x.as_dict for x in self.videos] or None,
                'files': [x.as_dict for x in self.files] or None,
            }
            self.cache('_attachments', attachments)
        return attachments

    def get_relations(self):
        """
        Returns relations for a Single or Group product.
        """
        if not self.is_variant:
            if not hasattr(self, '_relations'):
                self.cache('_relations', self.relations.all())
            return getattr(self, '_relations')

    def get_related_products(self, kind=None):
        """
        Returns related products with the given kind. Variants inherit their
        related products from a Group.
        """
        if self.is_variant:
            return self.group.get_related_products(kind)
        relations = self.get_relations()
        if kind is not None:
            relations = relations.filter(kind=kind)
        return [x.product for x in relations]

    def get_reviews(self, language=None, include_inactive=False):
        """
        Returns reviews for this product, uses the group product for varaints.
        """
        if not self.is_variant:
            reviews = getattr(self, '_reviews', None)
            if include_inactive:
                reviews = self.reviews.all()
            if reviews is None:
                reviews = self.reviews.active()
                self.cache('_reviews', reviews)
            if language is not None:
                return reviews.filter(language=language)
            return reviews

    def get_variant(self, attrs):
        """
        Returns a Variant with the given attribute values for this Group.
        eg. attrs = {'code': 'value', 'code2': 'value2'}
        """
        if self.is_group:
            for variant in self.get_variants():
                current = [(x['code'], x['value']) for x in variant.get_attributes().values()]
                if (sorted(attrs.items()) == sorted(current)):
                    return variant

    def filter_variants(self, attrs):
        """
        Returns a list of Variant products for this Group that contain
        attribute values passed in as `attrs`.

        eg. attrs = {'code': 'value', 'code2': 'value2'}
        """
        if self.is_group:
            variants = []
            for variant in self.get_variants():
                valid = True
                current = [(x['code'], x['value']) for x in variant.get_attributes().values()]
                for attr in attrs.items():
                    if attr not in current:
                        valid = False
                        break
                if valid:
                    variants.append(variant)
            return variants

    def create_variant(self, combo, language=None):
        """
        Create a variant with the given `combo` object from
        the `get_combinations` method.
        """
        if self.is_group:
            if not language:
                language = get_current_language()
            slug = combo['slug']
            code = combo['code'] or Product.objects.latest('pk').pk + 1
            num = 0
            while Product.objects.translated(slug=slug).exists():
                num = num + 1
                slug = '%s-%d' % (combo['slug'], num)
            while Product.objects.filter(code=code, translations__language_code=language).exists():
                code = int(code) + 1
            variant, created = Product.objects.get_or_create(code=code, kind=Product.VARIANT, group=self)
            variant.set_current_language(language)
            variant.name = combo['name']
            variant.slug = slug
            variant.save()
            if created:
                for attr_value in combo['attributes'].values():
                    attr = Attribute.objects.get(code=attr_value['code'])
                    if attr_value['value'] == '' and attr.nullable:
                        choice = None
                    else:
                        choice = attr.choices.get(pk=attr_value['choice'])
                    AttributeValue.objects.create(attribute=attr, product=variant, choice=choice)
            return variant

    @method_decorator(transaction.atomic)
    def create_all_variants(self, language=None):
        """
        Creates all missing variants for the group.
        """
        if self.is_group:
            variants = []
            if not language:
                language = get_current_language()
            for combo in self.get_combinations():
                if not combo['pk'] or language not in combo['languages']:
                    variants.append(self.create_variant(combo, language=language))
            return variants

    def get_attr(self, name, case=None, translated=False):
        """
        Returns groups attribute for variants if case is True.
        Caches the attribute.
        """
        if not hasattr(self, '_%s' % name):
            attr = self.safe_translation_getter(name) or case if translated else getattr(self, name, case)
            if self.is_variant and attr == case:
                if translated:
                    attr = self.group.safe_translation_getter(name) or attr
                else:
                    attr = getattr(self.group, name, attr)
            self.cache('_%s' % name, attr)
        return getattr(self, '_%s' % name)

    def cache(self, key, value):
        """
        Used in place of `setattr` to cache an attribute.
        Keeps a list of cached attributes so that they can be cleared later.
        """
        cached = getattr(self, '_cached_attrs', [])
        if key not in cached:
            cached.append(key)
        setattr(self, key, value)
        setattr(self, '_cached_attrs', cached)

    def clear(self, *attrs):
        """
        Clears cached attributes for this instance. Optionally pass in
        specific attributes to clear.
        """
        cached = getattr(self, '_cached_attrs', [])
        attrs = [x for x in attrs if x in cached] if attrs else cached
        for attr in attrs:
            delattr(self, attr)
            cached.remove(attr)
        setattr(self, '_cached_attrs', cached)

    def clean(self):
        kinds = dict([(0, 'single'), (1, 'group'), (2, 'variant')])
        getattr(self, '_clean_%s' % kinds[self.kind])()

    def _clean_single(self):
        if self.group_id:
            raise ValidationError(EM['group_has_group'])
        if self.variants.exists():
            raise ValidationError(EM['not_group_has_variants'])

    def _clean_group(self):
        if self.group_id:
            raise ValidationError(EM['group_has_group'])

    def _clean_variant(self):
        if self._category_id or self._brand_id or self._manufacturer_id:
            raise ValidationError(EM['variant_has_category'])
        if self._tax_id:
            raise ValidationError(EM['variant_has_tax'])
        if not self.group_id:
            raise ValidationError(EM['variant_no_group'])
        if self.group.is_variant:
            raise ValidationError(EM['varinat_group_variant'])
        if self.variants.exists():
            raise ValidationError(EM['not_group_has_variants'])


class AttributeQuerySet(TranslatableQuerySet):
    def active(self):
        return self.filter(active=True)


@python_2_unicode_compatible
class Attribute(TranslatableModel):
    """
    Used to define different types of attributes to be assigned on a Product
    variant. Eg. For a t-shirt attributes could be size, color, pattern etc.
    """
    TEMPLATES = ATTRIBUTE_TEMPLATES

    translations = TranslatedFields(
        name=models.CharField(_('Name'), max_length=128),
    )

    code = models.SlugField(_('Code'), max_length=128, unique=True, help_text=_(
        "An identifier that's used to access this attribute. Must be unique."))

    template = models.CharField(_('Template'), max_length=255, blank=True, null=True, choices=TEMPLATES, help_text=_(
        'You can specify a template for rendering this attribute or leave it empty for the default (dropdown) look.'))

    nullable = models.BooleanField(_('Nullable'), default=False, help_text=_(
        'Check this if you want to make "empty" an option for this Attribute.'))

    active = models.BooleanField(_('Active'), default=True, help_text=_('Is this attribute publicly visible.'))
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)
    order = models.PositiveIntegerField(_('Sort'), default=0)

    objects = AttributeQuerySet.as_manager()

    class Meta:
        db_table = 'shopit_attributes'
        verbose_name = _('Attribute')
        verbose_name_plural = _('Attributes')
        ordering = ['order']

    def __str__(self):
        name = self.safe_translation_getter('name', any_language=True)
        if Attribute.objects.translated(name=name).count() > 1:
            return '%s (%s)' % (name, self.code)
        return name

    def get_choices(self):
        """
        Returns choices adding in an empty one if attribute is nullable.
        """
        choices = getattr(self, '_choices', None)
        if choices is None:
            choices = list(self.choices.all())
            if self.nullable:
                choices.insert(0, AttributeChoice(attribute=self, value=''))
            setattr(self, '_choices', choices)
        return choices

    @property
    def key(self):
        return self.code.replace('-', '_')

    @cached_property
    def as_dict(self):
        return {
            'name': self.safe_translation_getter('name', any_language=True),
            'code': self.code,
            'template': self.template,
            'nullable': self.nullable,
            'order': self.order,
        }


@python_2_unicode_compatible
class AttributeChoice(TranslatableModel):
    """
    Choices of a particular attribute.
    """
    attribute = models.ForeignKey(Attribute, models.CASCADE, related_name='choices', verbose_name=_('Attribute'))

    translations = TranslatedFields(
        name=models.CharField(_('Name'), max_length=128, blank=True),
    )

    value = models.CharField(_('Value'), max_length=255)
    file = FilerFileField(blank=True, null=True, verbose_name=_('File'))
    order = models.PositiveIntegerField(_('Sort'), default=0)

    class Meta:
        db_table = 'shopit_attribute_choices'
        verbose_name = _('Choice')
        verbose_name_plural = _('Choices')
        unique_together = [('attribute', 'value')]
        ordering = ['order']

    def __str__(self):
        return self.safe_translation_getter('name') or self.value or '-'


@python_2_unicode_compatible
class AttributeValue(models.Model):
    """
    Through model for Product attributes.
    """
    attribute = models.ForeignKey(Attribute, models.CASCADE, related_name='values', verbose_name=_('Attribute'))
    product = models.ForeignKey(Product, models.CASCADE, related_name='attribute_values', verbose_name=_('Product'))
    choice = models.ForeignKey(AttributeChoice, models.CASCADE, blank=True, null=True, verbose_name=_('Value'))

    class Meta:
        db_table = 'shopit_attribute_values'
        verbose_name = _('Attribute Value')
        verbose_name_plural = _('Attribute Values')
        unique_together = ['attribute', 'product']
        ordering = ['attribute__order']

    def __str__(self):
        return self.label or '-'

    @property
    def label(self):
        return str(self.choice) if self.choice else '-'

    @property
    def value(self):
        return self.choice.value if self.choice else ''

    @property
    def file(self):
        return self.choice.file.url if self.choice and self.choice.file else None

    @cached_property
    def as_dict(self):
        data = {
            'choice': self.choice_id,
            'label': self.label,
            'value': self.value,
            'file': self.file,
        }
        data.update(self.attribute.as_dict)
        return data


@python_2_unicode_compatible
class Attachment(models.Model):
    """
    Product attachment model.
    """
    IMAGE, VIDEO, FILE = ('image', 'video', 'file')

    KINDS = (
        (IMAGE, _('Image')),
        (VIDEO, _('Video')),
        (FILE, _('File')),
    )

    EXTENSIONS = {
        IMAGE: ['jpg', 'jpeg', 'png', 'gif'],
        VIDEO: ['webm', 'ogv', 'ogg', 'mp4', 'm4p', 'm4v', 'flv', 'f4v'],
        FILE: ['pdf', 'doc', 'docx', 'ppt', 'pptx', 'txt'],
    }

    product = models.ForeignKey(Product, models.CASCADE, related_name='attachments', verbose_name=_('Product'))
    kind = models.CharField(_('Kind'), max_length=16, choices=KINDS, default=IMAGE)
    file = FilerFileField(on_delete=models.CASCADE, blank=True, null=True, verbose_name=_('File'))
    url = models.URLField(_('Url'), blank=True)
    order = models.PositiveIntegerField(_('Sort'), default=0)

    class Meta:
        db_table = 'shopit_attachments'
        verbose_name = _('Attachment')
        verbose_name_plural = _('Attachments')
        ordering = ['order']

    def __str__(self):
        return self.label

    def save(self, *args, **kwargs):
        self.clean()
        super(Attachment, self).save(*args, **kwargs)

    @property
    def label(self):
        return self.file.label if self.file else basename(self.value)

    @property
    def value(self):
        return self.file.url if self.file else self.url

    @cached_property
    def as_dict(self):
        attachment = {
            'label': self.label,
            'url': self.value,
            'order': self.order,
        }
        if EASY_THUMBNAILS and self.kind == self.IMAGE and self.file is not None:
            try:
                thumbnailer = get_thumbnailer(self.file)
                for alias, options in aliases.all(target='shopit.Attachment').items():
                    attachment['url_%s' % alias] = thumbnailer.get_thumbnail(options).url
            except InvalidImageFormatError:
                pass
        return attachment

    def clean(self):
        if self.file:
            if self.file.extension not in self.EXTENSIONS[self.kind]:
                raise ValidationError('%s (%s)' % (EM['wrong_extension'], ', '.join(self.EXTENSIONS[self.kind])))
        elif not self.url:
            raise ValidationError(EM['no_attachment_or_url'])


@python_2_unicode_compatible
class Relation(models.Model):
    """
    Inline product relation model.
    """
    KINDS = RELATION_KINDS

    base = models.ForeignKey(Product, models.CASCADE, related_name='relations')

    product = models.ForeignKey(
        Product, models.CASCADE, verbose_name=_('Product'),
        limit_choices_to={'kind__in': [Product.SINGLE, Product.GROUP]})

    kind = models.CharField(_('Kind'), max_length=128, blank=True, choices=KINDS)

    order = models.PositiveIntegerField(_('Sort'), default=0)

    class Meta:
        db_table = 'shopit_relations'
        verbose_name = _('Relation')
        verbose_name_plural = _('Relations')
        unique_together = [('base', 'product', 'kind')]
        ordering = ['order']

    def __str__(self):
        return self.product.product_name

    def save(self, *args, **kwargs):
        self.clean()
        super(Relation, self).save(*args, **kwargs)

    def clean(self):
        if self.base.is_variant or self.product.is_variant:
            raise ValidationError(EM['variant_has_relations'])
        if self.base == self.product:
            raise ValidationError(EM['relation_base_is_product'])


class ReviewQuerySet(QuerySet):
    def active(self):
        return self.filter(active=True)


@python_2_unicode_compatible
class Review(models.Model):
    """
    Model for product reviews.
    """
    RATINGS = REVIEW_RATINGS

    product = models.ForeignKey(
        Product, models.CASCADE, related_name='reviews', verbose_name=_('Product'),
        limit_choices_to={'kind__in': [Product.SINGLE, Product.GROUP]})

    customer = models.ForeignKey(Customer, models.CASCADE, related_name='product_reviews', verbose_name=_('Customer'))
    name = models.CharField(_('Name'), max_length=128, blank=True)
    text = models.TextField(_('Text'), max_length=1024)
    rating = models.PositiveIntegerField(_('Rating'), choices=RATINGS, default=0)
    language = models.CharField(_('Language'), max_length=2, choices=settings.LANGUAGES, default=settings.LANGUAGES[0][0])  # noqa

    active = models.BooleanField(_('Active'), default=True, help_text=_('Is this review publicly visible.'))
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)
    order = models.PositiveIntegerField(_('Sort'), default=0)

    objects = ReviewQuerySet.as_manager()

    class Meta:
        db_table = 'shopit_reviews'
        verbose_name = _('Review')
        verbose_name_plural = _('Reviews')
        ordering = ['-order']

    def __str__(self):
        return truncatewords(self.text, 3)

    def get_absolute_url(self):
        try:
            return reverse('shopit-product-review-detail', args=[self.product.safe_translation_getter('slug'), self.id])  # noqa
        except NoReverseMatch:  # pragma: no cover
            pass
