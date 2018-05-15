# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import json

from django.contrib.admin.sites import AdminSite
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.utils.formats import date_format
from django.utils.http import urlencode
from shop.money import Money

from shopit.admin.product import AttributeAdmin, ProductAdmin
from shopit.models.product import Attribute, AttributeChoice, Product

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
        self.user.is_staff = self.user.is_superuser = True
        self.user.save()

    def admin_login(self):
        return self.client.force_login(self.user)

    def create_products_with_variants(self):
        """Create product with variations."""
        self.color = self.create_attribute('Color', ['black', 'white', 'gold'])
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
        self.assertIsNone(self.admin.get_variants_field(Product()))
        rendered = render_to_string('admin/shopit/product_variants_field.html', {
            'product': self.iphone7,
            'variant': self.iphone7_black,
        })
        self.assertEquals(self.admin.get_variants_field(self.iphone7_black), rendered)

    def test_add_variant(self):
        self.create_products_with_variants()
        self.admin_login()
        response = self.client.get(reverse('admin:shopit_product_add_variant', args=[self.iphone7.pk]))
        self.assertEquals(response.status_code, 302)
        # Next is third variant.
        data = {'name': 'iPhone 7 #3', 'kind': 2, 'group': self.iphone7.pk}
        url_match = '{0}?{1}'.format(reverse('admin:shopit_product_add'), urlencode(data))
        self.assertEquals(response.url, url_match)

    def test_create_variant(self):
        self.create_products_with_variants()
        self.admin_login()
        # Cobo index out of range.
        url = reverse('admin:shopit_product_create_variant', args=[self.iphone7.pk, 10])
        self.assertEquals(self.client.get(url).status_code, 400)
        # Create variant.
        response = self.client.get(reverse('admin:shopit_product_create_variant', kwargs={
            'pk': self.iphone7.pk,
            'combo': 2,  # third combo index / "gold iphone".
        }))
        self.assertEquals(response.status_code, 302)
        variants = self.iphone7.get_variants()
        self.assertEquals(variants.count(), 3)  # there should be 3 variants now.
        url_match = '{0}?{1}'.format(
            reverse('admin:shopit_product_change', args=[4]),  # 3rd variant id.
            urlencode({'language': 'en'}),
        )
        self.assertEquals(response.url, url_match)

    def test_delete_variant(self):
        self.create_products_with_variants()
        self.admin_login()
        # Delete "iPhone 7 black" variant.
        self.assertEquals(self.iphone7.get_variants().count(), 2)
        response = self.client.get(reverse('admin:shopit_product_delete_variant', kwargs={
            'pk': self.iphone7.pk,
            'variant': self.iphone7_black.pk,
        }))
        self.assertEquals(response.status_code, 302)
        self.assertEquals(response.url, reverse('admin:shopit_product_change', args=[self.iphone7.pk]))
        self.assertEquals(self.iphone7.get_variants().count(), 1)

    def test_create_all_variants(self):
        self.admin_login()
        size = self.create_attribute('Size', ['L', 'XL'])
        color = self.create_attribute('Color', ['Black', 'White'])
        product = self.create_product('Shirt', Product.GROUP, 100)
        product.available_attributes.add(size, color)
        self.assertEquals(product.get_variants().count(), 0)
        response = self.client.get(reverse('admin:shopit_product_create_all_variants', args=[product.pk]))
        self.assertEquals(response.status_code, 302)
        self.assertEquals(response.url, reverse('admin:shopit_product_change', args=[product.pk]))
        product.clear('_variants')  # clear variants from cache.
        self.assertEquals(product.get_variants().count(), 4)

    def test_delete_invalid_variants(self):
        self.create_products_with_variants()
        self.admin_login()
        # Delete a "black" attribute choice to invalidate "iPhone 7 Black"
        black_id = self.iphone7_black.pk
        AttributeChoice.objects.get(value='black').delete()
        response = self.client.get(reverse('admin:shopit_product_delete_invalid_variants', args=[self.iphone7.pk]))
        self.assertEquals(response.status_code, 302)
        self.assertEquals(response.url, reverse('admin:shopit_product_change', args=[self.iphone7.pk]))
        self.assertIsNone(Product.objects.filter(id=black_id).first())
        self.assertEquals(self.iphone7.get_variants().count(), 1)

    def test_get_attribute_choices(self):
        self.admin_login()
        size = self.create_attribute('Size', ['L', 'XL'])
        data = {'attribute_id': size.pk}
        url = '{0}?{1}'.format(reverse('admin:shopit_product_get_attribute_choices'), urlencode(data))
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEquals(data['choices'][0]['label'], 'L')
        self.assertEquals(data['choices'][1]['label'], 'XL')
        # Test empty choices when no attribute
        response = self.client.get(reverse('admin:shopit_product_get_attribute_choices'))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(len(json.loads(response.content.decode('utf-8'))['choices']), 0)

    def test_make_active(self):
        self.admin_login()
        self.create_product('p1')
        self.create_product('p2', active=False)
        self.assertEquals(Product.objects.active().count(), 1)
        url = reverse('admin:shopit_product_changelist')
        response = self.client.post(url, {
            'action': 'make_active',
            '_selected_action': Product.objects.all().values_list('pk', flat=True),
        })
        self.assertEquals(response.status_code, 302)
        self.assertEquals(Product.objects.active().count(), 2)

    def test_make_inactive(self):
        self.admin_login()
        self.create_product('p1')
        self.create_product('p2')
        self.create_product('p3', active=False)
        self.assertEquals(Product.objects.active().count(), 2)
        url = reverse('admin:shopit_product_changelist')
        response = self.client.post(url, {
            'action': 'make_inactive',
            '_selected_action': Product.objects.all().values_list('pk', flat=True),
        })
        self.assertEquals(response.status_code, 302)
        self.assertEquals(Product.objects.active().count(), 0)
