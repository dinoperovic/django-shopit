# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from adminsortable2.admin import SortableAdminMixin
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from parler.admin import TranslatableAdmin

from shopit.models.tax import Tax


@admin.register(Tax)
class TaxAdmin(SortableAdminMixin, TranslatableAdmin):
    list_display = ['name', 'percent', 'language_column']
    fieldsets = [(_('Basic info'), {'fields': ['name', 'percent']})]

    class Media:
        css = {'all': ['shopit/css/djangocms-admin-style.css']}
