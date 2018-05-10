# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.contrib.admin.sites import AdminSite

from shopit.admin.categorization import CategoryAdmin
from shopit.models.categorization import Category

from ..utils import ShopitTestCase


class CategoryAdminTest(ShopitTestCase):
    def setUp(self):
        self.create_request()
        self.site = AdminSite(name="admin")
        self.admin = CategoryAdmin(Category, self.site)

    def test_get_name(self):
        c1 = self.create_categorization('category', 'C1')
        c2 = self.create_categorization('category', 'C2', parent=c1)
        template = '<div style="text-indent:{}px">{}</div>'
        self.assertEquals(self.admin.get_name(c1), template.format(0, 'C1'))
        self.assertEquals(self.admin.get_name(c2), template.format(1 * self.admin.mptt_level_indent, 'C2'))

    def test_get_list_display(self):
        list_display = list(self.admin.get_list_display(self.request))
        self.assertEquals(list_display[-3], '_tax')

    def test_get_fieldsets(self):
        fieldsets = list(self.admin.get_fieldsets(self.request, obj=None))
        self.assertEquals(fieldsets[-1][1]['fields'][-1], '_tax')
