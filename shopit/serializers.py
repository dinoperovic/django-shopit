# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.core.urlresolvers import NoReverseMatch, reverse
from django.template.loader import select_template
from django.utils import six
from measurement.base import MeasureBase
from measurement.measures import Distance, Mass
from phonenumber_field.serializerfields import PhoneNumberField
from rest_auth.serializers import PasswordResetConfirmSerializer, PasswordResetSerializer
from rest_framework import serializers
from shop.rest.money import MoneyField
from shop.serializers.bases import ProductSerializer as BaseProductSerializer
from shop.serializers.cart import CartItemSerializer as BaseCartItemSerializer
from shop.serializers.cart import ExtraCartRow as BaseExtraCartRow
from shop.serializers.cart import WatchItemSerializer as BaseWatchItemSerializer
from shop.serializers.defaults import AddToCartSerializer as BaseAddToCartSerializer
from shop.serializers.defaults import CustomerSerializer
from shop.serializers.order import OrderListSerializer as BaseOrderListSerializer

from shopit.conf import app_settings
from shopit.models.address import BillingAddress, ShippingAddress
from shopit.models.categorization import Brand, Category, Manufacturer
from shopit.models.customer import Customer
from shopit.models.flag import Flag
from shopit.models.modifier import Modifier
from shopit.models.product import Product, Relation, Review
from shopit.models.tax import Tax


class AccountSerializer(CustomerSerializer):
    id = serializers.IntegerField(source='pk')
    username = serializers.CharField(source='get_username')
    phone_number = PhoneNumberField()
    shipping_addresses = serializers.SerializerMethodField()
    billing_addresses = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = [
            'id', 'username', 'salutation', 'first_name', 'last_name', 'email', 'phone_number', 'extra',
            'shipping_addresses', 'billing_addresses']

    def get_shipping_addresses(self, obj):
        addresses = obj.shippingaddress_set.all()
        if addresses:
            return ShippingAddressSerializer(addresses, context=self.context, many=True).data

    def get_billing_addresses(self, obj):
        addresses = obj.billingaddress_set.all()
        if addresses:
            return BillingAddressSerializer(addresses, context=self.context, many=True).data


class AccountSummarySerializer(AccountSerializer):
    def get_fields(self):
        fields = super(AccountSummarySerializer, self).get_fields()
        del fields['username']
        del fields['email']
        del fields['phone_number']
        del fields['extra']
        return fields


class AccountResetSerializer(PasswordResetSerializer):
    def get_email_options(self):
        subject_template = select_template(['shopit/email/account_reset_subject.txt'])
        body_template = select_template(['shopit/email/account_reset_body.txt'])
        return {
            'subject_template_name': subject_template.template.name,
            'email_template_name': body_template.template.name
        }


class AccountResetConfirmSerializer(PasswordResetConfirmSerializer):
    pass


class AddressSerializerBase(serializers.ModelSerializer):
    class Meta:
        exclude = ['customer']


class OrderListSerializer(BaseOrderListSerializer):
    url = serializers.SerializerMethodField()

    def get_url(self, obj):
        url = obj.get_absolute_url()
        return self.context['request'].build_absolute_uri(url) if url else None


class ShippingAddressSerializer(AddressSerializerBase):
    class Meta(AddressSerializerBase.Meta):
        model = ShippingAddress


class BillingAddressSerializer(AddressSerializerBase):
    class Meta(AddressSerializerBase.Meta):
        model = BillingAddress


class TaxSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tax
        fields = ['id', 'name', 'percent']


class FlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flag
        fields = ['id', 'name', 'code', 'order']


class ModifierSerializer(serializers.ModelSerializer):
    amount = MoneyField()

    class Meta:
        model = Modifier
        fields = ['id', 'name', 'code', 'amount', 'percent', 'kind', 'order']


class CategorizationSerializerBase(serializers.ModelSerializer):
    """
    Base categorization serializer.
    Model and fields must be specified when extending.
    """
    class Meta:
        fields = ['id', 'name', 'slug', 'url', 'parent', 'modifiers', 'flags']

    url = serializers.SerializerMethodField()
    modifiers = ModifierSerializer(source='get_modifiers', many=True)
    flags = FlagSerializer(source='get_flags', many=True)

    def get_url(self, obj):
        url = obj.get_absolute_url()
        return self.context['request'].build_absolute_uri(url) if url else None


class CategorySerializer(CategorizationSerializerBase):
    tax = TaxSerializer()

    class Meta(CategorizationSerializerBase.Meta):
        model = Category
        fields = CategorizationSerializerBase.Meta.fields + ['tax']


class BrandSerializer(CategorizationSerializerBase):
    class Meta(CategorizationSerializerBase.Meta):
        model = Brand


class ManufacturerSerializer(CategorizationSerializerBase):
    class Meta(CategorizationSerializerBase.Meta):
        model = Manufacturer


class MeasureField(serializers.Field):
    """
    Custom serializer field to handle Measure objects.
    """
    def __init__(self, *args, **kwargs):
        assert 'measure' in kwargs, 'Missing `measure` argument.'
        self.measure = kwargs.pop('measure')
        assert not isinstance(self.measure, MeasureBase), 'Incorrect measure class.'
        super(MeasureField, self).__init__(*args, **kwargs)

    def to_representation(self, obj):
        return str(obj)

    def to_internal_value(self, data):
        data = data.split(' ')
        if not isinstance(data, six.text_type) and len(data) != 2:
            raise serializers.ValidationError('Got unexpected data.')
        return self.measure(**{data[1]: float(data[0])})


class RelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Relation
        exclude = []


class ReviewSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ['id', 'customer', 'name', 'text', 'rating', 'language', 'url', 'active', 'created_at', 'updated_at']

    def get_url(self, obj):
        url = obj.get_absolute_url()
        return self.context['request'].build_absolute_uri(url) if url else None


class ProductSerializer(BaseProductSerializer):
    """
    Base product serializer.
    """
    FIELDS = app_settings.PRODUCT_SERIALIZER_FIELDS

    url = serializers.SerializerMethodField(read_only=True)
    add_to_cart_url = serializers.SerializerMethodField(read_only=True)
    unit_price = MoneyField()
    tax = TaxSerializer()
    is_available = serializers.SerializerMethodField(read_only=True)
    category = CategorySerializer()
    brand = BrandSerializer()
    manufacturer = ManufacturerSerializer()
    modifiers = ModifierSerializer(source='get_modifiers', many=True)
    flags = FlagSerializer(source='get_flags', many=True)
    width = MeasureField(measure=Distance)
    height = MeasureField(measure=Distance)
    depth = MeasureField(measure=Distance)
    weight = MeasureField(measure=Mass)
    attributes = serializers.DictField(source='get_attributes', read_only=True)
    discount_amount = MoneyField(read_only=True)
    tax_amount = MoneyField(read_only=True)
    variants = serializers.SerializerMethodField()
    variations = serializers.ListField(source='get_variations', read_only=True)
    attachments = serializers.SerializerMethodField()
    relations = RelationSerializer(source='get_relations', many=True)
    reviews = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'caption', 'code', 'kind', 'url', 'add_to_cart_url', 'price', 'is_available',
            'description', 'unit_price', 'discount', 'tax', 'availability', 'category', 'brand', 'manufacturer',
            'discountable', 'modifiers', 'flags', 'width', 'height', 'depth', 'weight', 'available_attributes',
            'group',  'attributes', 'published', 'quantity', 'order', 'active', 'created_at', 'updated_at',
            'is_single', 'is_group', 'is_variant', 'is_discounted', 'is_taxed',  'discount_percent', 'tax_percent',
            'discount_amount', 'tax_amount', 'variants', 'variations', 'attachments', 'relations', 'reviews',
        ]

    def get_fields(self):
        fields = super(ProductSerializer, self).get_fields()
        included = list(set(self.FIELDS + self.get_included_fields()))
        for excluded in [x for x in fields if x not in included]:
            del fields[excluded]
        return fields

    def get_included_fields(self):
        return [x for x in self.context['request'].GET.get('include', '').split(',') if x in self.Meta.fields]

    def get_url(self, obj):
        url = obj.get_absolute_url()
        return self.context['request'].build_absolute_uri(url) if url else None

    def get_add_to_cart_url(self, obj):
        try:
            url = reverse('shopit-add-to-cart', args=[obj.safe_translation_getter('slug', any_language=True)])
            return self.context['request'].build_absolute_uri(url)
        except NoReverseMatch:
            return None

    def get_is_available(self, obj):
        return obj.is_available(request=self.context['request'])

    def get_variants(self, obj):
        variants = obj.get_variants()
        if variants:
            return ProductDetailSerializer(variants, context=self.context, many=True).data

    def get_attachments(self, obj):
        request = self.context['request']
        attachments = obj.get_attachments()
        for kind, items in [x for x in attachments.items() if x[1]]:
            for item in items:
                for key, value in item.items():
                    if key.startswith('url'):
                        item[key] = request.build_absolute_uri(value)
        return attachments

    def get_reviews(self, obj):
        reviews = obj.get_reviews(language=self.context['request'].LANGUAGE_CODE)
        if reviews:
            return ReviewSerializer(reviews, context=self.context, many=True).data


class ProductSummarySerializer(ProductSerializer):
    """
    Product list serializer is a Product serializer without some fields.
    """
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label', 'catalog')
        super(ProductSummarySerializer, self).__init__(*args, **kwargs)


class ProductDetailSerializer(ProductSerializer):
    FIELDS = app_settings.PRODUCT_DETAIL_SERIALIZER_FIELDS

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label', 'catalog')
        super(ProductDetailSerializer, self).__init__(*args, **kwargs)


class AddToCartSerializer(BaseAddToCartSerializer):
    is_available = serializers.ListField(read_only=True)

    def get_instance(self, context, data, extra_args):
        instance = super(AddToCartSerializer, self).get_instance(context, data, extra_args)
        product = context['product']
        request = context['request']
        quantity = int(request.GET.get('quantity', 1))
        instance.update({
            'quantity': quantity,
            'is_available': product.is_available(quantity, request),
        })
        return instance


class CartItemSerializer(BaseCartItemSerializer):
    pass


class WatchItemSerializer(BaseWatchItemSerializer):
    pass


class ExtraCartRow(BaseExtraCartRow):
    code = serializers.CharField(read_only=True, help_text="A code that's applied to the cart")
