# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from adminsortable2.admin import CustomInlineFormSet as SortableInlineFormSet
from django import forms
from django.forms.models import BaseInlineFormSet
from django.utils.module_loading import import_string
from parler.forms import TranslatableModelForm

from shopit.conf import app_settings
from shopit.models.product import AttributeValue, Product
from shopit.utils import get_error_message as em

try:
    TextEditor = import_string(app_settings.TEXT_EDITOR)
except ImportError:  # pragma: no cover
    from django.forms.widgets import Textarea as TextEditor


class ProductModelForm(TranslatableModelForm):
    class Meta:
        model = Product
        exclude = []
        widgets = {
            '_caption': forms.Textarea(attrs={'rows': 2}),
            '_description': TextEditor(),
        }

    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        queryset = Product.objects.translated(slug=slug)
        if self.instance.pk is not None:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError(em('duplicate_slug'))
        return slug

    def clean_kind(self):
        kind = self.cleaned_data.get('kind')
        if kind != Product.GROUP:
            if self.instance.variants.exists():
                raise forms.ValidationError(em('not_group_has_variants'))
        return kind

    def clean_category(self):
        return self._clean_categorization('category')  # pragma: no cover

    def clean_brand(self):
        return self._clean_categorization('brand')  # pragma: no cover

    def clean_manufacturer(self):
        return self._clean_categorization('manufacturer')  # pragma: no cover

    def clean__tax(self):
        tax = self.cleaned_data.get('_tax')
        kind = self.cleaned_data.get('kind')
        if kind == Product.VARIANT and tax is not None:
            raise forms.ValidationError(em('variant_has_tax'))
        return tax

    def clean_group(self):
        group = self.cleaned_data.get('group')
        kind = self.cleaned_data.get('kind')
        if group is None:
            if kind == Product.VARIANT:
                raise forms.ValidationError(em('variant_no_group'))
        else:
            if kind != Product.VARIANT:
                raise forms.ValidationError(em('group_has_group'))
            if group.is_variant:
                raise forms.ValidationError(em('varinat_group_variant'))
        return group

    def clean_available_attributes(self):
        attrs = self.cleaned_data.get('available_attributes')
        kind = self.cleaned_data.get('kind')
        if kind != Product.GROUP and attrs:
            raise forms.ValidationError(em('not_group_has_available_attributes'))
        elif kind == Product.GROUP and not attrs:
            raise forms.ValidationError(em('group_no_available_attributes'))
        return attrs

    def _clean_categorization(self, name):
        data = self.cleaned_data.get(name, None)
        kind = self.cleaned_data.get('kind')
        if data and kind == Product.VARIANT:
            raise forms.ValidationError(em('variant_has_category'))
        return data


class AttributeChoiceInlineFormSet(SortableInlineFormSet):
    def clean(self):
        super(AttributeChoiceInlineFormSet, self).clean()
        instance = getattr(self, 'instance', None)

        if any(self.errors) or instance is None:
            return

        clean_forms = [x for x in self.forms if 'value' in x.cleaned_data and not x.cleaned_data['DELETE']]
        if not clean_forms:
            raise forms.ValidationError(em('attribute_no_choices'))

        clean_values = [x.cleaned_data['value'] for x in clean_forms]
        if len(clean_values) != len(set(clean_values)):
            raise forms.ValidationError(em('attribute_duplicate_choices'))


class AttributeValueInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super(AttributeValueInlineFormSet, self).clean()
        instance = getattr(self, 'instance', None)

        if any(self.errors) or instance is None:
            return

        clean_forms = [x for x in self.forms if 'attribute' in x.cleaned_data and not x.cleaned_data['DELETE']]

        if instance.is_variant:
            if not clean_forms:
                raise forms.ValidationError(em('variant_no_attributes'))
            elif self.variant_exists(instance, clean_forms):
                raise forms.ValidationError(em('variant_already_exists'))
        elif clean_forms:
            raise forms.ValidationError(em('not_variant_has_attributes'))

    def variant_exists(self, variant, forms):
        """
        Checks if variant with this attributes already exists.
        """
        variations = [x[1] for x in variant.group.get_variations() if x[0] != variant.pk]
        if variations:
            attrs = {}
            for form in forms:
                del form.cleaned_data['DELETE']
                key = form.cleaned_data['attribute'].key
                attrs[key] = AttributeValue(**form.cleaned_data).as_dict
            return attrs in variations


class AttributeValueModelForm(forms.ModelForm):
    class Meta:
        model = AttributeValue
        fields = ['attribute', 'choice']

    def clean_choice(self):
        choice = self.cleaned_data.get('choice')
        attribute = self.cleaned_data.get('attribute')

        # Make sure correct choice is selected for the attribute.
        if attribute and not attribute.nullable:
            if choice not in attribute.get_choices():
                raise forms.ValidationError(em('incorrect_attribute_choice'))
        return choice
