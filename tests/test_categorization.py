# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.test import TestCase
from django.utils.text import slugify

from shopit.models.categorization import Brand, Category, Manufacturer


def create_categorization(model, name, depth=1, **kwargs):
    attrs = {
        'name': name,
        'slug': slugify(name),
    }
    attrs.update(kwargs)
    return model.objects.language().create(**attrs)


class TestCategorization(TestCase):
    def setUp(self):
        self.c1 = create_categorization(Category, 'C1')
        self.b1 = create_categorization(Brand, 'B1')
        self.m1 = create_categorization(Manufacturer, 'M1')

    def test__str__(self):
        self.assertEquals(str(self.c1), 'C1')

    def test_get_absolute_url(self):
        self.assertEquals(self.c1.get_absolute_url(), '/en/shopit/categories/c1/')
        self.assertEquals(self.b1.get_absolute_url(), '/en/shopit/brands/b1/')
        self.assertEquals(self.m1.get_absolute_url(), '/en/shopit/manufacturers/m1/')
