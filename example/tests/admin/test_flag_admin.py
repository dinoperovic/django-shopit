# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.contrib.admin.sites import AdminSite

from shopit.admin.flag import FlagAdmin
from shopit.models.flag import Flag

from ..utils import ShopitTestCase


class FlagAdminTest(ShopitTestCase):
    def setUp(self):
        self.create_request()
        self.site = AdminSite(name="admin")
        self.admin = FlagAdmin(Flag, self.site)

    def test_get_name(self):
        f1 = self.create_flag('F1')
        f2 = self.create_flag('F2', parent=f1)
        template = '<div style="text-indent:{}px">{}</div>'
        self.assertEquals(self.admin.get_name(f1), template.format(0, 'F1'))
        self.assertEquals(self.admin.get_name(f2), template.format(1 * self.admin.mptt_level_indent, 'F2'))
