# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from mptt.forms import MPTTAdminForm
from parler.forms import TranslatableModelForm

from shopit.models.categorization import Brand, Category, Manufacturer


class CategoryModelForm(MPTTAdminForm, TranslatableModelForm):
    class Meta:
        model = Category
        exclude = []


class BrandModelForm(MPTTAdminForm, TranslatableModelForm):
    class Meta:
        model = Brand
        exclude = []


class ManufacturerModelForm(MPTTAdminForm, TranslatableModelForm):
    class Meta:
        model = Manufacturer
        exclude = []
