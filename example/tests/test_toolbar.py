# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from cms.cms_toolbars import ADMIN_MENU_IDENTIFIER
from cms.middleware.toolbar import ToolbarMiddleware
from cms.api import create_page

from .utils import ShopitTestCase


class ToolbarTest(ShopitTestCase):
    def setUp(self):
        self.create_request()
        self.user.is_staff = self.user.is_superuser = True
        self.user.save()
        self.client.force_login(self.user)
        self.request.current_page = create_page('foo', 'default.html', 'en', published=True)
        ToolbarMiddleware().process_request(self.request)
        self.toolbar = self.request.toolbar

    def test_populate(self):
        self.toolbar.populate()

        # Test admin menu.
        admin_menu = self.toolbar.get_menu(ADMIN_MENU_IDENTIFIER)
        self.assertEquals(len(admin_menu.menus['shopit-admin-menu'].items), 11)

        # Test add menu.
        shopit_toolbar = self.toolbar.toolbars['shopit.cms_toolbars.ShopitToolbar']
        shopit_toolbar.is_current_app = True
        shopit_toolbar.populate()
        shopit_menu = self.toolbar.get_menu('shopit-menu')
        shopit_menu_add = shopit_menu.menus['shopit-menu-add']
        self.assertEquals(len(shopit_menu_add.items), 4)
