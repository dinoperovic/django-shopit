# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

# A dictionary with error messages used in Shopit.
ERROR_MESSAGES = getattr(settings, 'SHOPIT_ERROR_MESSAGES', {
    'duplicate_slug': _("This slug is already used. Try another one."),
    'group_has_group': _("Only variant products have a group."),
    'variant_no_group': _("Variants must have a group selected."),
    'variant_has_category': _("Variant products can't specify categorization. It's inherited from their group."),
    'varinat_group_variant': _("Can't set group to variant."),
    'not_group_has_variants': _("This product has variants, you need to delete them before changing it's kind."),
    'not_group_has_available_attributes': _("Only group products can have Availible attributes specified."),
    'group_no_available_attributes': _("Group product should have Availible attributes specified."),
    'variant_has_tax': _("Variant products can't specify tax, their group tax percentage will be used instead."),
    'variant_no_attributes': _("Variant must have their unique set of attributes specified."),
    'variant_already_exists': _("A Variant with this attributes for selected group already exists."),
    'not_variant_has_attributes': _("Only Variant products can have attributes."),
    'attribute_no_choices': _("Choices must be specified."),
    'attribute_duplicate_choices': _("Attribute can't have duplicate choices."),
    'incorrect_attribute_choice': _("Selected choice doesn't match the seleced attribute."),
    'no_attachment_or_url': _("Missing the attachment or url."),
    'wrong_extension': _("File extension not allowed for this attachment kind."),
    'discount_not_negative': _('A discount should be subtracting the price, amount or percent needs to be negative.'),
    'variant_has_relations': _('Only Single and Group products can have relations.'),
    'relation_base_is_product': _("You can't set relation to self."),
    'modifier_no_condition_path': _("You have to select a condition."),
    'cart_discount_code_exists': _("Code is already applied to your cart."),
    'cart_discount_code_invalid': _("Code is invalid or expired."),
    'cart_discount_code_wrong_customer': _("Code is invalid or expired."),
})

# Country choices used in checkout address forms. If empty all countries are
# used from ``shop.models.address.ISO_3166_CODES``.
ADDRESS_COUNTRIES = getattr(settings, 'SHOPIT_ADDRESS_COUNTRIES', ())

# A flag to control if customer's phone number is required.
PHONE_NUMBER_REQUIRED = getattr(settings, 'SHOPIT_PHONE_NUMBER_REQUIRED', False)

# A list of base serializer fields for a common product.
PRODUCT_SERIALIZER_FIELDS = getattr(settings, 'SHOPIT_PRODUCT_SERIALIZER_FIELDS', [
    'id', 'name', 'slug', 'caption', 'code', 'kind', 'url', 'add_to_cart_url', 'price', 'is_available',
])

# A list of serializer fields for a product detail.
PRODUCT_DETAIL_SERIALIZER_FIELDS = getattr(
    settings, 'SHOPIT_PRODUCT_DETAIL_SERIALIZER_FIELDS', PRODUCT_SERIALIZER_FIELDS + ['variants', 'attributes'])

# Template choices used when rendering an attribute.
ATTRIBUTE_TEMPLATES = getattr(settings, 'SHOPIT_ATTRIBUTE_TEMPLATES', ())

# Relation kind choices on a ``ProductRelation`` model.
RELATION_KINDS = getattr(settings, 'SHOPIT_RELATION_KINDS', (
    ('up-sell', _('Up-sell')),
    ('cross-sell', _('Cross-sell')),
))

# Rating choices for product reviews.
REVIEW_RATINGS = getattr(settings, 'SHOPIT_REVIEW_RATINGS', ())

# Is review active by default when created.
REVIEW_ACTIVE_DEFAULT = getattr(settings, 'SHOPIT_REVIEW_ACTIVE_DEFAULT', True)

# A list of ``ModifierCondition`` classes that will be used as choices for conditions in a Modifier.
MODIFIER_CONDITIONS = getattr(settings, 'SHOPIT_MODIFIER_CONDITIONS', [
    'shopit.modifier_conditions.PriceGreaterThanCondition',
    'shopit.modifier_conditions.PriceLessThanCondition',
    'shopit.modifier_conditions.QuantityGreaterThanCondition',
    'shopit.modifier_conditions.QuantityLessThanCondition',
])

# A text editor widget used to render a rich textarea in Shopit.
TEXT_EDITOR = getattr(settings, 'SHOPIT_TEXT_EDITOR', 'djangocms_text_ckeditor.widgets.TextEditorWidget')

# Load urls under a single ``ShopitApphook``, or leave the ability to add apps separately.
SINGLE_APPHOOK = getattr(settings, 'SHOPIT_SINGLE_APPHOOK', False)

# Designates if products of kind ``VARIANT`` should be included in attribute filtered results.
FILTER_ATTRIBUTES_INCLUDES_VARIANTS = getattr(settings, 'SHOPIT_FILTER_ATTRIBUTES_INCLUDES_VARIANTS', False)
