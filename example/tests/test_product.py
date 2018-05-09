# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from datetime import datetime

from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware

from shopit.models.cart import CartItem
from shopit.models.categorization import Brand, Category, Manufacturer
from shopit.models.product import Attachment, AttributeChoice, AttributeValue, Product, Review
from shopit.models.tax import Tax

from .utils import ShopitTestCase


class ProductManagerTest(ShopitTestCase):
    def setUp(self):
        self.p1 = self.create_product('P1')
        self.p2 = self.create_product('P3', Product.VARIANT, group=self.p1)

    def test_active(self):
        self.assertEquals(Product.objects.active().count(), 2)

    def test_top_level(self):
        self.assertEquals([self.p1], list(Product.objects.top_level()))


class ProductTest(ShopitTestCase):
    def setUp(self):
        self.create_request()

        self.tax = self.create_tax('Default Tax', 20)
        self.color = self.create_attribute('Color', ['black', 'white'])
        self.black_discount = self.create_modifier('Black Discount 30%', percent=-30)
        self.featured_flag = self.create_flag('Featured')

        # Singles.
        self.book = self.create_product('Book')
        self.headphones = self.create_product('Headphones')

        # Create iPhone 7.
        self.iphone7 = self.create_product(
            'iPhone 7', Product.GROUP, 700, tax=self.tax,
            category=self.create_categorization('category', 'Phones'),
            brand=self.create_categorization('brand', 'Apple'),
            manufacturer=self.create_categorization('manufacturer', 'Made in China'),
        )
        self.iphone7.available_attributes.add(self.color)
        self.iphone7.flags.add(self.featured_flag)
        self.create_relation(self.iphone7, self.headphones, kind='up-sell')
        self.create_review(self.iphone7, self.customer, text='iPhone review')
        [self.create_attachment(self.iphone7, 'image', url='image%s' % x) for x in range(2)]
        [self.create_attachment(self.iphone7, 'video', url='video%s' % x) for x in range(2)]
        [self.create_attachment(self.iphone7, 'file', url='file%s' % x) for x in range(2)]
        self.iphone7_black = self.create_product('iPhone 7 Black', Product.VARIANT, group=self.iphone7, quantity=3)
        self.iphone7_black.modifiers.add(self.black_discount)
        self.create_attribute_value(self.color, self.iphone7_black, self.color.get_choices()[0])
        self.iphone7_white = self.create_product('iPhone 7 White', Product.VARIANT, group=self.iphone7, discount=5)
        self.create_attribute_value(self.color, self.iphone7_white, self.color.get_choices()[1])

        # Make an invalid variant, it has no attributes.
        self.iphone7_invalid = self.create_product('iPhone 7 Invalid', Product.VARIANT, group=self.iphone7)

        # Add to cart.
        CartItem.objects.get_or_create(cart=self.cart, product=self.iphone7_black)

    def test__str__(self):
        self.assertEquals(str(self.iphone7), 'iPhone 7')

    def test_get_absolute_url(self):
        self.assertEquals(self.iphone7.get_absolute_url(), '/en/shopit/products/iphone-7/')

    def test_save(self):
        # Test that single is set to group once a variant is added.
        test = self.create_product('Test')
        self.create_product('Test Var', Product.VARIANT, group=test)
        self.assertTrue(test.is_group)

        # Test variant order is the same as group order.
        test.published = make_aware(parse_datetime('2016-01-01 00:00:00'))
        test.save()
        self.assertEquals(test.get_variants()[0].order, test.order)

    def test_product_name(self):
        self.assertEquals(self.iphone7.product_name, 'iPhone 7')

    def test_product_code(self):
        self.assertEquals(self.iphone7.product_code, 'iphone-7')

    def test_is_single(self):
        self.assertTrue(self.book.is_single)

    def test_is_group(self):
        self.assertTrue(self.iphone7.is_group)

    def test_is_variant(self):
        self.assertTrue(self.iphone7_black.is_variant)

    def test_setters(self):
        product, category, brand, manufacturer, tax = Product(), Category(), Brand(), Manufacturer(), Tax()
        product.category = category
        product.brand = brand
        product.manufacturer = manufacturer
        product.unit_price = 100
        product.discount = 5
        product.tax = tax
        product.width = 10
        product.height = 20
        product.depth = 30
        product.weight = 40
        self.assertEquals(product.category, category)
        self.assertEquals(product.brand, brand)
        self.assertEquals(product.manufacturer, manufacturer)
        self.assertEquals(product.unit_price, 100)
        self.assertEquals(product.discount, 5)
        self.assertEquals(product.tax, tax)
        self.assertEquals(int(product.width.value), 10)
        self.assertEquals(int(product.height.value), 20)
        self.assertEquals(int(product.depth.value), 30)
        self.assertEquals(int(product.weight.value), 40)

    def test_price(self):
        self.assertEquals(self.iphone7.price, self.iphone7.get_price())

    def test_is_discounted(self):
        self.assertFalse(self.iphone7.is_discounted)
        self.assertTrue(self.iphone7_white.is_discounted)

    def test_is_taxed(self):
        self.assertTrue(self.iphone7.is_taxed)
        self.assertFalse(self.book.is_taxed)

    def test_discount_percent(self):
        self.assertEquals(self.iphone7.discount_percent, 0)
        self.assertEquals(self.iphone7_white.discount_percent, 5)

    def test_tax_percent(self):
        self.assertEquals(self.book.tax_percent, 0)
        self.assertEquals(self.iphone7_black.tax_percent, 20)

    def test_discount_amount(self):
        self.assertEquals(self.iphone7_white.discount_amount, 35)
        self.assertEquals(self.iphone7.discount_amount, 0)

    def test_tax_amount(self):
        self.assertEquals(self.iphone7.tax_amount, 140)

    def test_primary_image(self):
        self.assertEquals(self.iphone7.primary_image.url, 'image0')

    def test_attachments(self):
        self.assertEquals(len(self.iphone7.images), 2)
        self.assertEquals(self.iphone7_black.videos, self.iphone7.videos)
        self.assertEquals(len(self.iphone7_white.files), 2)

    def test_get_price(self):
        self.assertEquals(self.iphone7_black.get_price(), 840)

    def test_get_availability(self):
        self.assertEquals(self.iphone7.get_availability(), [(0, datetime.max)])
        self.assertEquals(self.iphone7_black.get_availability(), [(3, datetime.max)])
        self.assertEquals(self.iphone7_invalid.get_availability(), [(0, datetime.max)])

    def test_is_available(self):
        self.assertEquals(self.iphone7_black.is_available(2), (True, 1))
        # When a request is passed, should count items in cart also.
        # 1 iPhone 7 Black is in cart.
        self.assertEquals(self.iphone7_black.is_available(2, self.request), (True, 0))

    def test_get_modifiers(self):
        self.assertEquals(len(self.iphone7.get_modifiers()), 0)
        self.assertEquals(len(self.iphone7_black.get_modifiers()), 1)

    def test_get_flags(self):
        iphone7_flags = self.iphone7.get_flags()
        self.assertEquals(len(iphone7_flags), 1)
        self.assertEquals(list(self.iphone7_black.get_flags()), list(iphone7_flags))

    def test_get_available_attributes(self):
        self.assertEquals(len(self.iphone7.get_available_attributes()), 1)

    def test_get_attributes(self):
        self.assertEquals(self.iphone7_black.get_attributes()['color']['value'], 'black')

    def test_get_variants(self):
        self.assertEquals(list(self.iphone7.get_variants()), [self.iphone7_black, self.iphone7_white])

    def test_get_invalid_variants(self):
        self.assertEquals(list(self.iphone7.get_invalid_variants()), [self.iphone7_invalid])

    def test_get_variations(self):
        self.assertEquals(len(self.iphone7.get_variations()), 2)

    def test_get_attribute_choices(self):
        iphone7_colors = [x['name'] for x in self.iphone7.get_attribute_choices()['color']['choices']]
        self.assertEquals(iphone7_colors, ['black', 'white'])

    def test_get_combinations(self):
        self.assertEquals([x['name'] for x in self.iphone7.get_combinations()], ['iPhone 7 Black', 'iPhone 7 White'])

    def test_get_attachments(self):
        iphone7_attachments = self.iphone7.get_attachments()
        self.assertEquals(len(iphone7_attachments['images']), 2)
        self.assertEquals(len(iphone7_attachments['videos']), 2)
        self.assertEquals(len(iphone7_attachments['files']), 2)
        self.assertEquals(self.iphone7_black.get_attachments(), iphone7_attachments)

    def test_get_relations(self):
        self.assertEquals(len(self.iphone7.get_relations()), 1)

    def test_get_related_products(self):
        iphone7_related_products = self.iphone7.get_related_products(kind='up-sell')
        self.assertEquals(iphone7_related_products[0].product_name, 'Headphones')
        self.assertEquals(self.iphone7_black.get_related_products(), iphone7_related_products)

    def test_get_reviews(self):
        self.assertEquals(len(self.iphone7.get_reviews()), 1)

    def test_get_variant(self):
        self.assertEquals(self.iphone7.get_variant({'color': 'black'}), self.iphone7_black)
        self.assertEquals(self.iphone7.get_variant({'color': 'white'}), self.iphone7_white)

    def test_filter_variants(self):
        self.assertEquals(self.iphone7.filter_variants({'color': 'black'}), [self.iphone7_black])

    def test_get_attr(self):
        self.assertEquals(self.iphone7_black.get_attr('_unit_price', 0), self.iphone7._unit_price)

    def test_cache(self):
        product = Product()
        product.cache('key', 'value')
        self.assertTrue(hasattr(product, 'key'))
        self.assertTrue('key' in getattr(product, '_cached_attrs'))
        product.clear('key')
        self.assertEquals(getattr(product, '_cached_attrs'), [])

    def test_clean(self):
        self.assertRaises(ValidationError, Product(group_id=1)._clean_single)
        self.book.variants = self.iphone7.get_variants()
        self.assertRaises(ValidationError, self.book._clean_single)
        self.assertRaises(ValidationError, Product(group_id=1)._clean_group)
        self.assertRaises(ValidationError, Product(_category_id=1)._clean_variant)
        self.assertRaises(ValidationError, Product(_tax_id=1)._clean_variant)
        self.assertRaises(ValidationError, Product(group_id=None)._clean_variant)
        self.assertRaises(ValidationError, Product(group=self.iphone7_black)._clean_variant)
        self.iphone7_white.variants = self.iphone7.get_variants()
        self.assertRaises(ValidationError, self.iphone7_white._clean_variant)


class AttributeTest(ShopitTestCase):
    def setUp(self):
        self.size = self.create_attribute('Size', range(10), nullable=True)
        self.color = self.create_attribute('Color', ['red', 'green', 'blue'])
        self.duplicate = self.create_attribute('Color', ['red', 'green', 'blue'], code='color-duplicate')

    def test__str__(self):
        self.assertEquals(str(self.size), 'Size')
        self.assertEquals(str(self.color), 'Color (color)')

    def test_get_choices(self):
        self.assertEquals(self.size.get_choices()[0].value, '')
        self.assertEquals(len(self.color.get_choices()), 3)

    def test_key(self):
        self.assertEquals(self.duplicate.key, 'color_duplicate')

    def test_attribute_choice(self):
        choices = list(AttributeChoice.objects.filter(attribute=self.color))
        self.assertEquals(self.color.get_choices(), choices)

    def test_attribute_value(self):
        value_null = AttributeValue(attribute=self.size, product=Product(), choice=self.size.get_choices()[0])
        value_zero = AttributeValue(attribute=self.size, product=Product(), choice=self.size.get_choices()[1])
        self.assertEquals(str(value_null), value_null.label)
        self.assertEquals(value_zero.value, '0')
        self.assertEquals(value_zero.file, None)


class AttachmentTest(ShopitTestCase):
    def setUp(self):
        self.product = self.create_product('Test')
        self.image0 = self.create_attachment(self.product, url='image0')

    def test__str__(self):
        self.assertEquals(str(self.image0), self.image0.label)

    def test_label(self):
        self.assertEquals(self.image0.label, 'image0')

    def test_value(self):
        self.assertEquals(self.image0.value, 'image0')

    def test_as_dict(self):
        # TODO: test thumbnails are created for aliases.
        pass

    def test_clean(self):
        # TODO: test extension.
        self.assertRaises(ValidationError, Attachment(url=None).clean)


class RelationTest(ShopitTestCase):
    def setUp(self):
        self.book = self.create_product('Book')
        self.pencil = self.create_product('Pencil')
        self.relation = self.create_relation(self.book, self.pencil, kind='up-sell')

    def test__str__(self):
        self.assertEquals(str(self.relation), 'Pencil')

    def test_clean(self):
        self.assertRaises(ValidationError, lambda: self.create_relation(Product(kind=Product.VARIANT), self.pencil))
        self.assertRaises(ValidationError, lambda: self.create_relation(self.book, self.book))


class ReviewTest(ShopitTestCase):
    def test__str__(self):
        self.assertEquals(str(Review(text='Testing')), 'Testing')
