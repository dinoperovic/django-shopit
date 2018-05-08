# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.utils.module_loading import import_string
from mptt.forms import MPTTAdminForm
from parler.forms import TranslatableModelForm

from shopit.conf import app_settings
from shopit.models.categorization import Brand, Category, Manufacturer

try:
    TextEditor = import_string(app_settings.TEXT_EDITOR)
except ImportError:
    from django.forms.widgets import Textarea as TextEditor


class CategoryModelForm(MPTTAdminForm, TranslatableModelForm):
    class Meta:
        model = Category
        exclude = []
        widgets = {'description': TextEditor()}


class BrandModelForm(MPTTAdminForm, TranslatableModelForm):
    class Meta:
        model = Brand
        exclude = []
        widgets = {'description': TextEditor()}


class ManufacturerModelForm(MPTTAdminForm, TranslatableModelForm):
    class Meta:
        model = Manufacturer
        exclude = []
        widgets = {'description': TextEditor()}
