# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django import forms
from mptt.forms import MPTTAdminForm
from parler.forms import TranslatableModelForm

from shopit.models.categorization import Brand, Category, Manufacturer


class CategoryModelForm(MPTTAdminForm, TranslatableModelForm):
    class Meta:
        model = Category
        exclude = []
        widgets = {'flags': forms.CheckboxSelectMultiple()}


class BrandModelForm(MPTTAdminForm, TranslatableModelForm):
    class Meta:
        model = Brand
        exclude = []
        widgets = {'flags': forms.CheckboxSelectMultiple()}


class ManufacturerModelForm(MPTTAdminForm, TranslatableModelForm):
    class Meta:
        model = Manufacturer
        exclude = []
        widgets = {'flags': forms.CheckboxSelectMultiple()}
