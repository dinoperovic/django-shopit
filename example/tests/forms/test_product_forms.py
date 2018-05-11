# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django import forms
from django.core.exceptions import ValidationError
from django.forms.models import inlineformset_factory

from shopit.forms.product import ProductModelForm, AttributeChoiceInlineFormSet, AttributeValueInlineFormSet
from shopit.models.product import Product, AttributeChoice, Attribute, AttributeValue

from ..utils import ShopitTestCase


class ProductModelFormTest(ShopitTestCase):
    def setUp(self):
        self.p1 = self.create_product('P1', kind=Product.GROUP)
        self.p1_var = self.create_product('P1 var', group=self.p1, kind=Product.VARIANT)

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
        formset_factory = inlineformset_factory(Attribute, AttributeChoice, formset=AttributeChoiceInlineFormSet, exclude=[])  # noqa
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
        formset.instance = None
        self.assertIsNone(formset.clean())  # No instance


class AttributeValueInlineFormSetTest(ShopitTestCase):
    def test__clean(self):
        p = self.create_product('P', kind=Product.GROUP)
        p_var = self.create_product('P var', group=p, kind=Product.VARIANT)

        formset_factory = inlineformset_factory(Product, AttributeValue, formset=AttributeValueInlineFormSet, exclude=[])  # noqa
        formset = formset_factory(instance=p_var)

        class DummyForm(forms.ModelForm):
            class Meta:
                model = AttributeValue
                exclude = []

            def __init__(self, *args, **kwargs):
                self.cleaned_data = kwargs.pop('cleaned_data')
                self.cleaned_data['DELETE'] = False
                super(DummyForm, self).__init__(*args, **kwargs)

        form1 = DummyForm(cleaned_data={'attribute': 1})
        form2 = DummyForm(cleaned_data={'attribute': 1})  # duplicate
        formset.forms = []
        self.assertRaises(ValidationError, formset.clean)  # no forms
        formset.forms = [form1, form2]
        # TODO: test variant exists

        formset.instance.kind = Product.SINGLE
        formset.instance.group = None
        formset.instance.save()
        self.assertRaises(ValidationError, formset.clean)  # not variant
        formset.instance = None
        self.assertIsNone(formset.clean())  # No instance

    def test_variant_exists(self):
        pass
