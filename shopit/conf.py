# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals


class DefaultSettings(object):  # pragma: no cover
    """
    Default settings for Shopit.
    """
    def _setting(self, name, default=None):
        from django.conf import settings
        return getattr(settings, name, default)

    @property
    def SHOPIT_ERROR_MESSAGES(self):
        """
        A dictionary with error messages used in Shopit.
        """
        from django.utils.translation import ugettext_lazy as _

        default = {
            'duplicate_slug': _("This slug is already used. Try another one."),
            'group_has_group': _("Only variant products have a group."),
            'variant_no_group': _("Variants must have a group selected."),
            'variant_has_category': _("Variant products can't specify categorization. It's inherited from their group."),  # noqa
            'varinat_group_variant': _("Can't set group to variant."),
            'not_group_has_variants': _("This product has variants, you need to delete them before changing it's kind."),  # noqa
            'not_group_has_available_attributes': _("Only group products can have Availible attributes specified."),
            'group_no_available_attributes': _("Group product should have Availible attributes specified."),
            'variant_has_tax': _("Variant products can't specify tax, their group tax percentage will be used instead."),  # noqa
            'variant_no_attributes': _("Variant must have their unique set of attributes specified."),
            'variant_already_exists': _("A Variant with this attributes for selected group already exists."),
            'not_variant_has_attributes': _("Only Variant products can have attributes."),
            'attribute_no_choices': _("Choices must be specified."),
            'attribute_duplicate_choices': _("Attribute can't have duplicate choices."),
            'incorrect_attribute_choice': _("Selected choice doesn't match the seleced attribute."),
            'no_attachment_or_url': _("Missing the attachment or url."),
            'wrong_extension': _("File extension not allowed for this attachment kind."),
            'discount_not_negative': _('A discount should be subtracting the price, amount or percent needs to be negative.'),  # noqa
            'variant_has_relations': _('Only Single and Group products can have relations.'),
            'relation_base_is_product': _("You can't set relation to self."),
            'modifier_no_condition_path': _("You have to select a condition."),
            'cart_discount_code_exists': _("Code is already applied to your cart."),
            'cart_discount_code_invalid': _("Code is invalid or expired."),
            'cart_discount_code_wrong_customer': _("Code is invalid or expired."),
        }
        default.update(self._setting('SHOPIT_ERROR_MESSAGES', {}))
        return default

    @property
    def SHOPIT_ADDRESS_COUNTRIES(self):
        """
        Country choices used in checkout address forms. If empty all countries
        are used from ``shop.models.address.ISO_3166_CODES``.
        """
        return self._setting('SHOPIT_ADDRESS_COUNTRIES', ())

    @property
    def SHOPIT_PRIMARY_ADDRESS(self):
        """
        A primary address to be used in a checkout proccess. Can be 'shipping'
        or 'billing'. Depending on wich address is selected, the other one will
        get the option to use the primary one instead of having to fill it out.
        """
        from django.core.exceptions import ImproperlyConfigured

        value = self._setting('SHOPIT_PRIMARY_ADDRESS', 'shipping')
        if value not in ['shipping', 'billing']:
            raise ImproperlyConfigured("Setting `SHOPIT_PRIMARY_ADDRESS` must be either 'shipping' or 'billing'.")
        return value

    @property
    def SHOPIT_PHONE_NUMBER_REQUIRED(self):
        """
        A flag to control if customer's phone number is required.
        """
        return self._setting('SHOPIT_PHONE_NUMBER_REQUIRED', False)

    @property
    def SHOPIT_PRODUCT_SERIALIZER_FIELDS(self):
        """
        A list of base serializer fields for a common product.
        """
        default = ['id', 'name', 'slug', 'caption', 'code', 'kind', 'url', 'add_to_cart_url', 'price', 'is_available']
        return self._setting('SHOPIT_PRODUCT_SERIALIZER_FIELDS', default)

    @property
    def SHOPIT_PRODUCT_DETAIL_SERIALIZER_FIELDS(self):
        """
        A list of serializer fields for a product detail.
        """
        default = list(set(self.PRODUCT_SERIALIZER_FIELDS + ['variants', 'attributes']))
        return self._setting('SHOPIT_PRODUCT_DETAIL_SERIALIZER_FIELDS', default)

    @property
    def SHOPIT_ATTRIBUTE_TEMPLATES(self):
        """
        Template choices used when rendering an attribute.
        """
        return self._setting('SHOPIT_ATTRIBUTE_TEMPLATES', ())

    @property
    def SHOPIT_RELATION_KINDS(self):
        """
        Relation kind choices on a ``ProductRelation`` model.
        """
        from django.utils.translation import ugettext_lazy as _

        default = (
            ('up-sell', _('Up-sell')),
            ('cross-sell', _('Cross-sell')),
        )
        return self._setting('SHOPIT_RELATION_KINDS', default)

    @property
    def SHOPIT_REVIEW_RATINGS(self):
        """
        Rating choices for product reviews.
        """
        return self._setting('SHOPIT_REVIEW_RATINGS', ())

    @property
    def SHOPIT_REVIEW_ACTIVE_DEFAULT(self):
        """
        Is review active by default when created.
        """
        return self._setting('SHOPIT_REVIEW_ACTIVE_DEFAULT', True)

    @property
    def SHOPIT_ASYNC_PRODUCT_LIST(self):
        """
        A boolean that enables you to optimize ``ProductListView`` and
        ``CategoryDetailView`` when products are fetched asynchronously (ajax).
        """
        return self._setting('SHOPIT_ASYNC_PRODUCT_LIST', False)

    @property
    def SHOPIT_ADD_PRODUCT_LIST_TO_CONTEXT(self):
        """
        A boolean to control if ``product_list`` is added to context when
        accessing a ``ProductListView`` or ``CategoryDetailView``.
        """
        return self._setting('SHOPIT_ADD_PRODUCT_LIST_TO_CONTEXT', not self.SHOPIT_ASYNC_PRODUCT_LIST)

    @property
    def SHOPIT_DEFAULT_PRODUCT_ORDER(self):
        """
        A default product list ordering.
        Must be on of 'name|-name|price|-price'.
        """
        from django.core.exceptions import ImproperlyConfigured

        value = self._setting('SHOPIT_DEFAULT_PRODUCT_ORDER', None)
        if value not in [None, 'name', '-name', 'price', '-price']:
            raise ImproperlyConfigured("Setting `SHOPIT_DEFAULT_PRODUCT_ORDER` must be 'name|-name|price|-price'.")
        return value

    @property
    def SHOPIT_FLAG_TEMPLATES(self):
        """
        Template choices used when rendering a Flag.
        """
        return self._setting('SHOPIT_FLAG_TEMPLATES', ())

    @property
    def SHOPIT_MODIFIER_CONDITIONS(self):
        """
        A list of ``ModifierCondition`` classes that will be used as choices
        for conditions in a Modifier.
        """
        default = [
            'shopit.modifier_conditions.PriceGreaterThanCondition',
            'shopit.modifier_conditions.PriceLessThanCondition',
            'shopit.modifier_conditions.QuantityGreaterThanCondition',
            'shopit.modifier_conditions.QuantityLessThanCondition',
        ]
        return self._setting('SHOPIT_MODIFIER_CONDITIONS', default)

    @property
    def SHOPIT_TEXT_EDITOR(self):
        """
        A text editor widget used to render a rich textarea in Shopit.
        """
        return self._setting('SHOPIT_TEXT_EDITOR', 'djangocms_text_ckeditor.widgets.TextEditorWidget')

    @property
    def SHOPIT_SINGLE_APPHOOK(self):
        """
        Load urls under a single ``ShopitApphook``, or leave the ability to
        add apps separately.
        """
        return self._setting('SHOPIT_SINGLE_APPHOOK', False)

    @property
    def SHOPIT_FILTER_ATTRIBUTES_INCLUDES_VARIANTS(self):
        """
        Designates if products of kind ``VARIANT`` should be included in
        attribute filtered results.
        """
        return self._setting('SHOPIT_FILTER_ATTRIBUTES_INCLUDES_VARIANTS', False)

    def __getattr__(self, key):
        if not key.startswith('SHOPIT_'):
            key = 'SHOPIT_{0}'.format(key)
        return getattr(self, key)


app_settings = DefaultSettings()
