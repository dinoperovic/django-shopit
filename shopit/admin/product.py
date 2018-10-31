# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from adminsortable2.admin import SortableAdminMixin, SortableInlineAdminMixin
from cms.admin.placeholderadmin import FrontendEditableAdminMixin, PlaceholderAdminMixin
from cms.utils.i18n import get_current_language
from django.conf.urls import url
from django.contrib import admin, messages
from django.contrib.admin.views.main import ChangeList
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.utils import IntegrityError
from django.http import HttpResponseBadRequest, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.utils.encoding import smart_text
from django.utils.formats import date_format
from django.utils.html import format_html
from django.utils.http import urlencode
from django.utils.translation import ugettext_lazy as _
from mptt.admin import TreeRelatedFieldListFilter
from parler.admin import TranslatableAdmin, TranslatableTabularInline

from shopit.forms.product import (AttributeChoiceInlineFormSet, AttributeValueInlineFormSet, AttributeValueModelForm,
                                  ProductModelForm)
from shopit.models.product import Attachment, Attribute, AttributeChoice, AttributeValue, Product, Relation, Review


class AttributeChoiceInline(SortableInlineAdminMixin, TranslatableTabularInline, admin.TabularInline):
    model = AttributeChoice
    formset = AttributeChoiceInlineFormSet
    fields = ['name', 'value', 'file', 'order']
    extra = 0


@admin.register(Attribute)
class AttributeAdmin(SortableAdminMixin, TranslatableAdmin):
    list_display = ['get_name', 'code', 'nullable', 'active', 'language_column']
    readonly_fields = ['created_at', 'updated_at']
    search_fields = ['code', 'translations__name', 'template']

    fieldsets = [
        (_('Basic info'), {'fields': ['name', 'code']}),
        (_('Status'), {'fields': [('active', 'created_at', 'updated_at')]}),
        (_('Settings'), {'fields': ['template', 'nullable']}),
    ]

    inlines = [AttributeChoiceInline]

    class Media:
        css = {'all': ['shopit/css/djangocms-admin-style.css']}

    def get_prepopulated_fields(self, request, obj=None):
        return {'code': ['name']}  # pragma: no cover

    def get_name(self, obj):
        return str(obj)
    get_name.admin_order_field = 'translations__name'
    get_name.short_description = _('Name')

    def get_template(self, obj):
        return obj.template or None
    get_template.admin_order_field = 'template'
    get_template.short_description = _('Template')


class AttributeValueInline(admin.TabularInline):
    model = AttributeValue
    form = AttributeValueModelForm
    formset = AttributeValueInlineFormSet
    extra = 0


class AttachmentInline(SortableInlineAdminMixin, admin.TabularInline):
    model = Attachment
    extra = 0


class RelationInline(SortableInlineAdminMixin, admin.TabularInline):
    model = Relation
    fk_name = 'base'
    raw_id_fields = ['product']
    extra = 0


class ReviewInline(SortableInlineAdminMixin, admin.TabularInline):
    model = Review
    extra = 0
    fields = ['customer', 'name', 'text', 'rating', 'active']
    readonly_fields = ['customer', 'name', 'text', 'rating', 'created_at']

    def has_add_permission(self, request):
        return False  # pragma: no cover


class ProductChangeList(ChangeList):
    """
    Override ChangeList to filter out Variant products from admin list
    but include them in search results.
    """
    def get_queryset(self, request):
        qs = super(ProductChangeList, self).get_queryset(request)
        if request.GET.get('q'):
            return qs.order_by('-order', 'kind', 'published')
        return qs.filter(kind__in=[Product.SINGLE, Product.GROUP])


@admin.register(Product)
class ProductAdmin(FrontendEditableAdminMixin, PlaceholderAdminMixin, TranslatableAdmin):
    form = ProductModelForm
    list_display = ['get_name', 'get_slug', 'code', 'get_is_group', 'get_unit_price', 'get_discount_percent',
                    'get_tax_percent', 'get_price', 'get_published', 'active', 'language_column']

    list_filter = ['published',
                   ('_category', TreeRelatedFieldListFilter),
                   ('_brand', TreeRelatedFieldListFilter),
                   ('_manufacturer', TreeRelatedFieldListFilter)]

    search_fields = ['code', 'translations__name']
    raw_id_fields = ['group']
    readonly_fields = ['created_at', 'updated_at', 'get_summary_field', 'get_variants_field']
    filter_horizontal = ['modifiers', 'flags', 'available_attributes']

    frontend_editable_fields = [
        'name', 'slug', 'code', 'active', 'created_at', 'updated_at', 'published', '_caption', '_description',
        '_category', '_brand', '_manufacturer', '_unit_price', '_discount', '_tax', 'quantity', 'kind', 'discountable',
        'modifiers', 'flags', '_width', '_height', '_depth', '_weight', 'available_attributes', 'group']

    fieldsets = [
        (_('Basic info'), {'fields': ['name', 'slug', 'code']}),
        (_('Status'), {'fields': [('active', 'created_at', 'updated_at'), 'published']}),
        (_('Description'), {'fields': ['_caption', '_description']}),
        (_('Categorization'), {
            'fields': ['_category', '_brand', '_manufacturer'],
            'description': _('This section is ment for Single and Group products. Variants will inherit their '
                             'categorization from their Group.')}),
        (_('Pricing'), {'fields': ['_unit_price', '_discount', '_tax', 'get_summary_field']}),
        (_('Stock'), {'fields': ['quantity']}),
        (_('Settings'), {'fields': ['kind', 'discountable', 'modifiers', 'flags']}),
        (_('Measurements'), {
            'fields': [('_width', '_height'), ('_depth', '_weight')],
            'description': _('Measurements of a product, mostly used for delivery calculations. Variants can leave '
                             'this section empty to inherit the values from their Group.')}),
        (_('Group'), {'fields': ['available_attributes']}),
        (_('Variants'), {'fields': ['group', 'get_variants_field']}),
    ]

    inlines = [AttributeValueInline, AttachmentInline, RelationInline, ReviewInline]
    actions = ['make_active', 'make_inactive']

    class Media:
        css = {'all': ['shopit/css/djangocms-admin-style.css']}
        js = ['shopit/js/product_admin.js']

    def get_prepopulated_fields(self, request, obj=None):
        return {'slug': ['name']}  # pragma: no cover

    def get_changelist(self, request, **kwargs):
        return ProductChangeList

    def get_changeform_initial_data(self, request):
        initial = super(ProductAdmin, self).get_changeform_initial_data(request)
        try:
            latest = Product.objects.latest('pk')
            initial['code'] = latest.pk + 1
        except Product.DoesNotExist:
            initial['code'] = 1
        return initial

    def get_urls(self):
        urls = super(ProductAdmin, self).get_urls()  # pragma: no cover
        return [
            url(r'^get-attribute-choices/$', self.admin_site.admin_view(self.get_attribute_choices),
                name='shopit_product_get_attribute_choices'),
            url(r'^(?P<pk>\d+)/add-variant/$', self.admin_site.admin_view(self.add_variant),
                name='shopit_product_add_variant'),
            url(r'^(?P<pk>\d+)/create-variant/(?P<combo>\d+)/$', self.admin_site.admin_view(self.create_variant),
                name='shopit_product_create_variant'),
            url(r'^(?P<pk>\d+)/delete-variant/(?P<variant>\d+)/$', self.admin_site.admin_view(self.delete_variant),
                name='shopit_product_delete_variant'),
            url(r'^(?P<pk>\d+)/create-all-variants/$', self.admin_site.admin_view(self.create_all_variants),
                name='shopit_product_create_all_variants'),
            url(r'^(?P<pk>\d+)/delete-invalid-variants/$', self.admin_site.admin_view(self.delete_invalid_variants),
                name='shopit_product_delete_invalid_variants'),
        ] + urls  # pragma: no cover

    def get_name(self, obj):
        if obj.is_variant:
            return '--- %s' % smart_text(obj)
        return smart_text(obj)
    get_name.admin_order_field = 'translations__name'
    get_name.short_description = _('Name')

    def get_slug(self, obj):
        return obj.safe_translation_getter('slug')
    get_slug.allow_tags = True
    get_slug.admin_order_field = 'translations__slug'
    get_slug.short_description = _('Slug')

    def get_is_group(self, obj):
        return obj.is_group
    get_is_group.boolean = True
    get_is_group.admin_order_field = 'kind'
    get_is_group.short_description = _('Group')

    def get_unit_price(self, obj):
        return str(obj.unit_price)
    get_unit_price.short_description = _('Unit price')

    def get_discount_percent(self, obj):
        return '%g%%' % obj.discount_percent
    get_discount_percent.admin_order_field = 'discount'
    get_discount_percent.short_description = _('Discount %')

    def get_tax_percent(self, obj):
        return '%g%%' % obj.tax_percent
    get_tax_percent.admin_order_field = 'tax__percent'
    get_tax_percent.short_description = _('Tax %')

    def get_price(self, obj):
        return str(obj.price)
    get_price.short_description = _('Price')

    def get_published(self, obj):
        return date_format(obj.published, 'SHORT_DATETIME_FORMAT')
    get_published.admin_order_field = 'order'
    get_published.short_description = _('Published')

    def get_summary_field(self, obj):
        unit_price = '%s: %s' % (_('Unit price'), smart_text(obj.unit_price))
        discount = '%s: %g%%' % (_('Discount percent'), obj.discount_percent)
        tax = '%s: %g%%' % (_('Tax percent'), obj.tax_percent)
        price = '<strong>%s: %s</strong>' % (_('Price'), smart_text(obj.price))
        return format_html('<br>'.join([unit_price, discount, tax, price]))
    get_summary_field.allow_tags = True
    get_summary_field.short_description = _('Summary')

    def get_variants_field(self, obj):
        if not obj.pk:
            return None
        return render_to_string('admin/shopit/product_variants_field.html', {
            'product': obj.group or obj,
            'variant': obj if obj.group else None,
        })
    get_variants_field.allow_tags = True
    get_variants_field.short_description = _('Variants')

    def add_variant(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        product = product.group or product
        variants = product.get_variants()
        num = variants.count() + 1 if variants else 1
        name = '%s #%s' % (product.product_name, num)
        data = {'name': name, 'kind': Product.VARIANT, 'group': product.pk}
        return HttpResponseRedirect('{}?{}'.format(reverse('admin:shopit_product_add'), urlencode(data)))

    def create_variant(self, request, pk, combo, message=True, product=None, language=None):
        """
        This view creates a full variant with it's attribute values
        based on a combination index passed in as `combo`.
        """
        product = product or get_object_or_404(Product, pk=pk)
        product = product.group or product
        if not language:
            language = get_current_language()  # pragma: no cover
        try:
            combo = product.get_combinations()[int(combo)]
            variant = product.create_variant(combo, language=language)
        except (IndexError, ObjectDoesNotExist, IntegrityError):
            return HttpResponseBadRequest()
        if message:
            messages.success(request, _('Variant successfully created.'))  # pragma: no cover
        return HttpResponseRedirect(
            reverse('admin:shopit_product_change', args=[variant.pk]) + '?language=%s' % language)

    def delete_variant(self, request, pk, variant, message=True, product=None):
        product = product or get_object_or_404(Product, pk=pk)
        product = product.group or product
        variant = get_object_or_404(product.get_variants(), pk=variant)
        variant.delete()
        if message:
            messages.success(request, _('Variant successfully deleted.'))  # pragma: no cover
        return HttpResponseRedirect(reverse('admin:shopit_product_change', args=[product.pk]))

    def create_all_variants(self, request, pk, language=None):
        product = get_object_or_404(Product, pk=pk)
        product = product.group or product
        product.create_all_variants(language=language)
        messages.success(request, _('Variants successfully created.'))
        return HttpResponseRedirect(reverse('admin:shopit_product_change', args=[product.pk]))

    @method_decorator(transaction.atomic)
    def delete_invalid_variants(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        product = product.group or product
        for invalid in product.get_invalid_variants():
            invalid.delete()
        messages.success(request, _('Invalid variants successfully deleted.'))
        return HttpResponseRedirect(reverse('admin:shopit_product_change', args=[product.pk]))

    def get_attribute_choices(self, request):
        """
        A Json response view that's used to fetch the attribute choices
        and update the attribute values select field on a product variant.
        """
        attribute_id = request.GET.get('attribute_id', None) or None
        try:
            attribute = Attribute.objects.get(id=attribute_id)
            choices = [{'id': x.pk, 'label': str(x)} for x in attribute.get_choices()]
        except Attribute.DoesNotExist:
            choices = []
        return JsonResponse({'choices': choices})

    def make_active(self, request, queryset):
        rows = queryset.update(active=True)
        if rows == 1:
            msg = _('1 Product was successfully marked as active.')  # pragma: no cover
        else:
            msg = _('%s Products were successfully marked as active.') % rows
        self.message_user(request, msg, messages.SUCCESS)
    make_active.short_description = _('Mark selected Products as active')

    def make_inactive(self, request, queryset):
        rows = queryset.update(active=False)
        if rows == 1:
            msg = _('1 Product was successfully marked as inactive.')  # pragma: no cover
        else:
            msg = _('%s Products were successfully marked as inactive.') % rows
        self.message_user(request, msg, messages.SUCCESS)
    make_inactive.short_description = _('Mark selected Products as inactive')
