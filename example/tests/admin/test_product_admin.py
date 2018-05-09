# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.contrib.admin.sites import AdminSite
from django.template.loader import render_to_string
from django.utils.formats import date_format
from shop.money import Money

from shopit.admin.product import AttributeAdmin, ProductAdmin
from shopit.models.product import Attribute, Product

from ..utils import ShopitTestCase


class AttributeAdminTest(ShopitTestCase):
    def setUp(self):
        self.create_request()
        self.site = AdminSite()
        self.color = self.create_attribute('Color', template='test_template.html')
        self.admin = AttributeAdmin(Attribute, self.site)

    def test_get_name(self):
        self.assertEquals(self.admin.get_name(self.color), 'Color')

    def test_get_template(self):
        self.assertEquals(self.admin.get_template(self.color), 'test_template.html')


class ProductAdminTest(ShopitTestCase):
    def setUp(self):
        self.create_request()
        self.site = AdminSite(name="admin")
        self.admin = ProductAdmin(Product, self.site)

    def create_products_with_variants(self):
        """Create product with variations."""
        self.color = self.create_attribute('Color', ['black', 'white'])
        self.iphone7 = self.create_product(
            'iPhone 7', Product.GROUP, 700,
            category=self.create_categorization('category', 'Phones'),
            brand=self.create_categorization('brand', 'Apple'),
            manufacturer=self.create_categorization('manufacturer', 'Made in China'),
        )
        self.iphone7.available_attributes.add(self.color)
        self.iphone7_black = self.create_product('iPhone 7 Black', Product.VARIANT, group=self.iphone7, quantity=3)
        self.create_attribute_value(self.color, self.iphone7_black, self.color.get_choices()[0])
        self.iphone7_white = self.create_product('iPhone 7 White', Product.VARIANT, group=self.iphone7, discount=5)
        self.create_attribute_value(self.color, self.iphone7_white, self.color.get_choices()[1])

    def test_changelist(self):
        """When searching variants should appear along site groups and singles."""
        self.create_products_with_variants()
        cl_class = self.admin.get_changelist(self.request)
        cl_args = self.get_changelist_args(self.admin, list_select_related=self.admin.get_list_select_related(self.request))  # noqa
        cl = cl_class(self.request, Product, *cl_args)
        self.assertEquals(cl.get_queryset(self.request).count(), 1)
        new_request = self.factory.get('/?q=i')
        self.assertEquals(cl.get_queryset(new_request).count(), 3)

    def test_get_changeform_initial_data(self):
        p = self.create_product('P')
        data = self.admin.get_changeform_initial_data(self.request)
        self.assertEquals(data['code'], 2)
        p.delete()
        data = self.admin.get_changeform_initial_data(self.request)
        self.assertEquals(data['code'], 1)

    def test_get_name(self):
        self.create_products_with_variants()
        self.assertEquals(self.admin.get_name(self.iphone7), 'iPhone 7')
        self.assertEquals(self.admin.get_name(self.iphone7_black), '--- iPhone 7 Black')

    def test_get_slug(self):
        p = self.create_product('product 1')
        self.assertEquals(self.admin.get_slug(p), 'product-1')

    def test_get_is_group(self):
        self.create_products_with_variants()
        self.assertTrue(self.admin.get_is_group(self.iphone7))
        self.assertFalse(self.admin.get_is_group(self.iphone7_black))

    def test_get_unit_price(self):
        p = self.create_product('P', unit_price=120)
        self.assertEquals(self.admin.get_unit_price(p), str(Money(120)))

    def test_get_discount_percent(self):
        p = self.create_product('P', _discount=10)
        self.assertEquals(self.admin.get_discount_percent(p), '10%')

    def test_get_tax_percent(self):
        p = self.create_product('P', tax=self.create_tax('Tax', percent=10))
        self.assertEquals(self.admin.get_tax_percent(p), '10%')

    def test_get_price(self):
        p = self.create_product('P', unit_price=300)
        self.assertEquals(self.admin.get_price(p), str(Money(300)))

    def test_get_published(self):
        p = self.create_product('P', unit_price=300)
        self.assertEquals(self.admin.get_published(p), date_format(p.published, 'SHORT_DATETIME_FORMAT'))

    def test_get_summary_field(self):
        p = self.create_product('P', unit_price=120)
        result = ("Unit price: \u20ac 120.00<br>"
                  "Discount percent: 0%<br>"
                  "Tax percent: 0%<br>"
                  "<strong>Price: \u20ac 120.00</strong>")
        self.assertEquals(self.admin.get_summary_field(p), result)

    def test_get_variants_field(self):
        self.create_products_with_variants()
        rendered = render_to_string('admin/shopit/product_variants_field.html', {
            'product': self.iphone7,
            'variant': self.iphone7_black,
        })
        self.assertEquals(self.admin.get_variants_field(self.iphone7_black), rendered)
