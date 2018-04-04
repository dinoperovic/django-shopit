# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from mptt.admin import DraggableMPTTAdmin
from parler.admin import TranslatableAdmin

from shopit.forms.flag import FlagModelForm
from shopit.models.flag import Flag


@admin.register(Flag)
class FlagAdmin(TranslatableAdmin, DraggableMPTTAdmin):
    form = FlagModelForm
    list_display = ['tree_actions', 'get_name', 'code', 'active', 'language_column']
    list_display_links = ['get_name']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = [
        (_('Basic info'), {'fields': ['name', 'code']}),
        (_('Status'), {'fields': [('active', 'created_at', 'updated_at')]}),
        (_('Settings'), {'fields': ['parent']}),
    ]

    class Media:
        css = {'all': ['shopit/css/djangocms-admin-style.css']}

    def get_prepopulated_fields(self, request, obj=None):
        return {'code': ['name']}

    def get_name(self, obj):
        return format_html(
            '<div style="text-indent:{}px">{}</div>',
            obj.level * self.mptt_level_indent, obj.safe_translation_getter('name', any_language=True))
    get_name.short_description = _('Name')
