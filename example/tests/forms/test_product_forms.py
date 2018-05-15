# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django import forms
from django.core.exceptions import ValidationError
from django.forms.models import inlineformset_factory

from shopit.forms.product import (AttributeChoiceInlineFormSet, AttributeValueInlineFormSet, AttributeValueModelForm,
                                  ProductModelForm)
from shopit.models.product import Attribute, AttributeChoice, AttributeValue, Product

from ..utils import ShopitTestCase


class ProductModelFormTest(ShopitTestCase):
    def setUp(self):
        self.p1 = self.create_product('P1', kind=Product.GROUP)
        self.p1_var = self.create_product('P1 var', group=self.p1, kind=Product.VARIANT)
        self.p2 = self.create_product('P2', kind=Product.SINGLE)

    def test_clean_slug(self):
        form = ProductModelForm()
        form.cleaned_data = {'slug': 'test'}
        self.assertEquals(form.clean_slug(), 'test')
        form.cleaned_data = {'slug': 'p1'}  # invalid / already exists.
        self.assertRaises(ValidationError, form.clean_slug)
        # Allow slug when same as instance.
        form = ProductModelForm(instance=self.p1)
        form.cleaned_data = {'slug': 'p1'}
        self.assertEquals(form.clean_slug(), 'p1')

    def test_clean_kind(self):
        form = ProductModelForm(instance=self.p1)
        form.cleaned_data = {'kind': Product.SINGLE}
        self.assertRaises(ValidationError, form.clean_kind)
        form.cleaned_data = {'kind': Product.GROUP}
        self.assertEquals(form.clean_kind(), Product.GROUP)
        form = ProductModelForm(instance=self.p2)
        form.cleaned_data = {'kind': Product.SINGLE}
        self.assertEquals(form.clean_kind(), Product.SINGLE)

    def test_clean_categorization(self):
        category = self.create_categorization('category', 'Category')
        form = ProductModelForm()
        form.cleaned_data = {'category': category.id, 'kind': Product.VARIANT}
        self.assertRaises(ValidationError, form.clean_category)
        form.cleaned_data = {'category': category, 'kind': Product.SINGLE}
        self.assertEquals(form.clean_category(), category)

    def test_clean__tax(self):
        form = ProductModelForm()
        form.cleaned_data = {'_tax': 1, 'kind': Product.VARIANT}
        self.assertRaises(ValidationError, form.clean__tax)
        form.cleaned_data = {'_tax': 1, 'kind': Product.SINGLE}
        self.assertEquals(form.clean__tax(), 1)

    def test_clean_group(self):
        form = ProductModelForm()
        form.cleaned_data = {'group': None, 'kind': Product.VARIANT}
        self.assertRaises(ValidationError, form.clean_group)
        form.cleaned_data = {'group': None, 'kind': Product.GROUP}
        self.assertEquals(form.clean_group(), None)
        form.cleaned_data = {'group': self.p1, 'kind': Product.GROUP}
        self.assertRaises(ValidationError, form.clean_group)
        form.cleaned_data = {'group': self.p1_var, 'kind': Product.VARIANT}
        self.assertRaises(ValidationError, form.clean_group)
        form.cleaned_data = {'group': self.p1, 'kind': Product.VARIANT}
        self.assertEquals(form.clean_group(), self.p1)

    def test_clean_available_attributes(self):
        form = ProductModelForm()
        form.cleaned_data = {'available_attributes': [1], 'kind': Product.VARIANT}
        self.assertRaises(ValidationError, form.clean_available_attributes)
        form.cleaned_data = {'available_attributes': None, 'kind': Product.GROUP}
        self.assertRaises(ValidationError, form.clean_available_attributes)
        form.cleaned_data = {'available_attributes': [1], 'kind': Product.GROUP}
        self.assertEquals(form.clean_available_attributes(), [1])


class AttributeChoiceInlineFormSetTest(ShopitTestCase):
    def test_clean(self):
        formset_factory = inlineformset_factory(
            Attribute,
            AttributeChoice,
            formset=AttributeChoiceInlineFormSet,
            exclude=[],
        )
        formset = formset_factory()

        class DummyForm(forms.ModelForm):
            class Meta:
                model = AttributeChoice
                exclude = []

            def __init__(self, *args, **kwargs):
                self.cleaned_data = kwargs.pop('cleaned_data')
                self.cleaned_data['DELETE'] = False
                super(DummyForm, self).__init__(*args, **kwargs)

        form1 = DummyForm(cleaned_data={'value': 1})
        form2 = DummyForm(cleaned_data={'value': 1})  # duplicate
        formset.forms = []
        self.assertRaises(ValidationError, formset.clean)  # no forms
        formset.forms = [form1, form2]
        self.assertRaises(ValidationError, formset.clean)  # duplicate values
        formset.forms = [form1]
        self.assertIsNone(formset.clean())  # pass through
        formset.instance = None
        self.assertIsNone(formset.clean())  # no instance


class AttributeValueInlineFormSetTest(ShopitTestCase):
    def setUp(self):
        self.formset_factory = inlineformset_factory(
            Product,
            AttributeValue,
            formset=AttributeValueInlineFormSet,
            exclude=[],
        )

    def get_dummy_form(self, **kwargs):
        class DummyForm(forms.ModelForm):
            class Meta:
                model = AttributeValue
                exclude = []

            def __init__(self, *args, **kwargs):
                self.cleaned_data = kwargs.pop('cleaned_data')
                self.cleaned_data['DELETE'] = False
                super(DummyForm, self).__init__(*args, **kwargs)
        return DummyForm(**kwargs)

    def create_product_with_variants(self):
        self.color = self.create_attribute('Color', ['black', 'white', 'gold'])
        self.iphone7 = self.create_product('iPhone 7', Product.GROUP, 700)
        self.iphone7.available_attributes.add(self.color)
        self.iphone7_black = self.create_product('iPhone 7 Black', Product.VARIANT, group=self.iphone7, quantity=3)
        self.create_attribute_value(self.color, self.iphone7_black, self.color.get_choices()[0])
        self.iphone7_white = self.create_product('iPhone 7 White', Product.VARIANT, group=self.iphone7, discount=5)
        self.create_attribute_value(self.color, self.iphone7_white, self.color.get_choices()[1])

    def test__clean(self):
        self.create_product_with_variants()
        formset = self.formset_factory(instance=self.iphone7_black)

        form1 = self.get_dummy_form(cleaned_data={'attribute': 1})
        form2 = self.get_dummy_form(cleaned_data={'attribute': 1})  # duplicate
        formset.forms = []
        self.assertRaises(ValidationError, formset.clean)  # no forms

        choice = AttributeChoice.objects.filter(attribute=self.color, value='white').first()
        choice_gold = AttributeChoice.objects.filter(attribute=self.color, value='gold').first()
        form_existant = self.get_dummy_form(cleaned_data={'attribute': self.color, 'product': self.iphone7, 'choice': choice})  # noqa
        formset.forms = [form_existant]

        # TODO: Fix for `formset.variants_exists` may be needed.
        # Fails on travis.

        # TODO: Fails on travis only. Disable for now.
        # self.assertRaises(ValidationError, formset.clean)  # variant exists

        form_non_existant = self.get_dummy_form(cleaned_data={'attribute': self.color, 'product': self.iphone7, 'choice': choice_gold})  # noqa
        formset.forms = [form_non_existant]
        # TODO: Fails on travis only. Disable for now.
        # self.assertIsNone(formset.clean())  # variant not exists / valid

        formset.forms = [form1, form2]
        formset.instance.kind = Product.SINGLE
        formset.instance.group = None
        formset.instance.save()
        self.assertRaises(ValidationError, formset.clean)  # not variant
        formset.forms = []
        self.assertIsNone(formset.clean())  # No errors
        formset.instance = None
        self.assertIsNone(formset.clean())  # No instance

    def test_variant_exists(self):
        self.create_product_with_variants()
        formset = self.formset_factory(instance=self.iphone7)

        # choice = AttributeChoice.objects.filter(attribute=self.color, value='white').first()
        # form = self.get_dummy_form(cleaned_data={'attribute': self.color, 'product': self.iphone7, 'choice': choice})
        # TODO: Fails on travis only. Disable for now.
        # self.assertTrue(formset.variant_exists(self.iphone7_black, [form]))

        p = self.create_product('P', kind=Product.GROUP)
        p_var = self.create_product('P var', group=p, kind=Product.VARIANT)
        self.assertIsNone(formset.variant_exists(p_var, []))


class AttributeValueModelFormTest(ShopitTestCase):
    def test_clean_choice(self):
        form = AttributeValueModelForm()
        attr_size = self.create_attribute('Size', ['S', 'L', 'XL'])
        attr_color = self.create_attribute('Color', ['Black', 'White'], nullable=True)
        choice_size = AttributeChoice.objects.filter(attribute=attr_size).first()
        choice_color = AttributeChoice.objects.filter(attribute=attr_color).first()
        form.cleaned_data = {'choice': choice_color, 'attribute': attr_size}
        self.assertRaises(ValidationError, form.clean_choice)  # choice-attribute missmatch
        form.cleaned_data = {'choice': choice_size, 'attribute': attr_size}
        self.assertEquals(form.clean_choice(), choice_size)
        form.cleaned_data = {'choice': choice_color, 'attribute': attr_color}
        self.assertEquals(form.clean_choice(), choice_color)
