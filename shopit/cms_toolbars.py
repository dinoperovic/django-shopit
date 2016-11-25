# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from cms.cms_toolbars import ADMIN_MENU_IDENTIFIER, ADMINISTRATION_BREAK
from cms.toolbar.items import Break, SubMenu
from cms.toolbar_base import CMSToolbar
from cms.toolbar_pool import toolbar_pool
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from shopit.models.categorization import Brand, Category, Manufacturer
from shopit.models.product import Product


@toolbar_pool.register
class ShopitToolbar(CMSToolbar):
    """
    djangoCMS toolbar for Shopit.
    """
    watch_models = [Product, Category, Brand, Manufacturer]

    def populate(self):
        admin_menu = self.toolbar.get_menu(ADMIN_MENU_IDENTIFIER)
        if admin_menu:
            position = admin_menu.get_alphabetical_insert_position(_('Shopit'), SubMenu)
            if not position:
                position = admin_menu.find_first(Break, identifier=ADMINISTRATION_BREAK) + 1
                admin_menu.add_break('shopit-break', position=position)

            menu = admin_menu.get_or_create_menu('shopit-admin-menu', _('Shopit'), position=position)

            product_changelist_url = reverse('admin:shopit_product_changelist')
            menu.add_sideframe_item(_('Product List'), url=product_changelist_url)
            product_add_url = reverse('admin:shopit_product_add')
            menu.add_modal_item(_('Add New Product'), url=product_add_url)
            menu.add_break()

            category_changelist_url = reverse('admin:shopit_category_changelist')
            menu.add_sideframe_item(_('Categories List'), url=category_changelist_url)
            category_add_url = reverse('admin:shopit_category_add')
            menu.add_modal_item(_('Add New Category'), url=category_add_url)
            menu.add_break()

            brand_changelist_url = reverse('admin:shopit_brand_changelist')
            menu.add_sideframe_item(_('Brands List'), url=brand_changelist_url)
            brand_add_url = reverse('admin:shopit_brand_add')
            menu.add_modal_item(_('Add New Brand'), url=brand_add_url)
            menu.add_break()

            manufacturer_changelist_url = reverse('admin:shopit_manufacturer_changelist')
            menu.add_sideframe_item(_('Manufacturers List'), url=manufacturer_changelist_url)
            manufacturer_add_url = reverse('admin:shopit_manufacturer_add')
            menu.add_modal_item(_('Add New Manufacturer'), url=manufacturer_add_url)

        if self.is_current_app:
            menu = self.toolbar.get_or_create_menu('shopit-menu', _('Shopit'))
            add_menu = menu.get_or_create_menu('shopit-menu-add', _('Add New'))

            add_menu.add_modal_item(_('Product'), url=product_add_url)
            add_menu.add_modal_item(_('Category'), url=category_add_url)
            add_menu.add_modal_item(_('Brand'), url=brand_add_url)
            add_menu.add_modal_item(_('Manufacturer'), url=manufacturer_add_url)
