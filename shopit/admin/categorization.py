# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import copy

from cms.admin.placeholderadmin import FrontendEditableAdminMixin, PlaceholderAdminMixin
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from mptt.admin import DraggableMPTTAdmin
from parler.admin import TranslatableAdmin

from shopit.forms.categorization import BrandModelForm, CategoryModelForm, ManufacturerModelForm
from shopit.models.categorization import Brand, Category, Manufacturer


class CategorizationAdminBase(FrontendEditableAdminMixin, PlaceholderAdminMixin,
                              TranslatableAdmin, DraggableMPTTAdmin):
    """
    Base admin for categorization models.
    """
    list_display = ['tree_actions', 'get_name', 'slug', 'active', 'language_column']
    list_display_links = ['get_name']
    filter_horizontal = ['modifiers', 'flags']
    readonly_fields = ['created_at', 'updated_at']

    frontend_editable_fields = [
        'name', 'slug', 'active', 'created_at', 'updated_at', 'description', '_featured_image', 'parent',
        'modifiers', 'flags']

    fieldsets = [
        (_('Basic info'), {'fields': ['name', 'slug']}),
        (_('Status'), {'fields': [('active', 'created_at', 'updated_at')]}),
        (_('Description'), {'fields': ['description']}),
        (_('Media'), {'fields': ['_featured_image']}),
        (_('Settings'), {'fields': ['parent', 'modifiers', 'flags']}),
    ]

    class Media:
        css = {'all': ['shopit/css/djangocms-admin-style.css']}

    def get_prepopulated_fields(self, request, obj=None):
        return {'slug': ['name']}

    def get_name(self, obj):
        return format_html(
            '<div style="text-indent:{}px">{}</div>',
            obj.level * self.mptt_level_indent, obj.safe_translation_getter('name', any_language=True))
    get_name.short_description = _('Name')


@admin.register(Category)
class CategoryAdmin(CategorizationAdminBase):
    form = CategoryModelForm
    frontend_editable_fields = CategorizationAdminBase.frontend_editable_fields + ['_tax']

    def get_list_display(self, request):
        list_display = list(super(CategoryAdmin, self).get_list_display(request))
        list_display.insert(-2, '_tax')
        return list_display

    def get_fieldsets(self, request, obj=None):
        fieldsets = copy.deepcopy(super(CategoryAdmin, self).get_fieldsets(request, obj))
        fieldsets[-1][1]['fields'].append('_tax')
        return fieldsets


@admin.register(Brand)
class BrandAdmin(CategorizationAdminBase):
    form = BrandModelForm


@admin.register(Manufacturer)
class ManufacturerAdmin(CategorizationAdminBase):
    form = ManufacturerModelForm
