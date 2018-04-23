# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from adminsortable2.admin import SortableAdminMixin, SortableInlineAdminMixin
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from parler.admin import TranslatableAdmin

from shopit.models.modifier import DiscountCode, Modifier, ModifierCondition


class ModifierConditionInline(SortableInlineAdminMixin, admin.TabularInline):
    model = ModifierCondition
    extra = 0


@admin.register(Modifier)
class ModifierAdmin(SortableAdminMixin, TranslatableAdmin):
    list_display = [
        'name', 'code', 'get_value', 'kind', 'get_requires_code', 'get_filtering_enabled', 'active', 'language_column']

    list_filter = ['kind']
    readonly_fields = ['created_at', 'updated_at', 'get_requires_code_field', 'get_filtering_enabled_field']

    fieldsets = [
        (_('Basic info'), {'fields': ['name', 'code']}),
        (_('Status'), {'fields': [('active', 'created_at', 'updated_at')]}),
        (_('Amounts'), {'fields': ['amount', 'percent']}),
        (_('Settings'), {'fields': ['kind', 'get_requires_code_field', 'get_filtering_enabled_field']}),
    ]

    inlines = [ModifierConditionInline]

    class Media:
        css = {'all': ['shopit/css/djangocms-admin-style.css']}

    def get_prepopulated_fields(self, request, obj=None):
        return {'code': ['name']}

    def get_value(self, obj):
        return '%s %%' % obj.percent if obj.percent else obj.amount
    get_value.short_description = _('Value')

    def get_requires_code(self, obj):
        return obj.requires_code
    get_requires_code.boolean = True
    get_requires_code.short_description = _('Codes')

    def get_filtering_enabled(self, obj):
        return obj.is_filtering_enabled
    get_filtering_enabled.boolean = True
    get_filtering_enabled.short_description = _('Filtering')

    def get_requires_code_field(self, obj):
        html = '<img src="/static/admin/img/icon-yes.svg" alt="True">'
        if not obj.requires_code:
            html = '<img src="/static/admin/img/icon-no.svg" alt="False">'
        help_text = _('Displays if code is required for the modifier to be valid. This value depends on '
                      'active codes that are assigned to this modifier.')
        return format_html('%s<p class="help">%s</p>' % (html, help_text))
    get_requires_code_field.allow_tags = True
    get_requires_code_field.short_description = _('Requires code')

    def get_filtering_enabled_field(self, obj):
        if obj.is_filtering_enabled:
            html = '<img src="/static/admin/img/icon-yes.svg" alt="True">'
        else:
            html = '<img src="/static/admin/img/icon-no.svg" alt="False">'
        help_text = _('Displays if modifier can be used as a filter to return products with this modifier selected. '
                      'Filtering is enabled when modifier is not a "Cart modifier", does not require any codes & '
                      'has no conditions to be met.')
        return format_html('%s<p class="help">%s</p>' % (html, help_text))
    get_filtering_enabled_field.allow_tags = True
    get_filtering_enabled_field.short_description = _('Filtering enabled')


@admin.register(DiscountCode)
class DiscountCodeAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ['code', 'modifier', 'num_uses', 'get_is_valid']
    list_filter = ['modifier']
    raw_id_fields = ['customer']
    readonly_fields = ['get_is_valid_field']

    fieldsets = [
        (_('Basic info'), {'fields': ['code', 'modifier']}),
        (_('Status'), {'fields': ['active']}),
        (_('Settings'), {'fields': ['customer', 'max_uses', 'num_uses', ('valid_from', 'valid_until')]}),
        (None, {'fields': ['get_is_valid_field']}),
    ]

    class Media:
        css = {'all': ['shopit/css/djangocms-admin-style.css']}

    def get_is_valid(self, obj):
        return obj.is_valid
    get_is_valid.boolean = True
    get_is_valid.admin_order_field = 'valid_from'
    get_is_valid.short_description = _('Is valid')

    def get_is_valid_field(self, obj):
        if obj.is_valid:
            html = '<img src="/static/admin/img/icon-yes.svg" alt="True">'
        else:
            html = '<img src="/static/admin/img/icon-no.svg" alt="False">'
        help_text = _('Displays if code is valid by checking that: code is active, times used is less than max '
                      'uses, is within the valid time period.')
        return format_html('%s<p class="help">%s</p>' % (html, help_text))
    get_is_valid_field.allow_tags = True
    get_is_valid_field.short_description = _('Is valid')
