Settings
########

Available settings to override.

----

Error messages
==============

A dictionary with error messages used in **Shopit**.

.. code:: python

    SHOPIT_ERROR_MESSAGES = {
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
    }

Address
=======

Country choices used in checkout address forms. If empty all countries are used from ``shopit.models.address.ISO_3166_CODES``.

.. code:: python

    SHOPIT_ADDRESS_COUNTRIES = ()


Customer
========

A flag to control if customer's phone number is required.

.. code:: python

    SHOPIT_PHONE_NUMBER_REQUIRED = False


Product
=======

A list of base serializer fields for a common product.

.. code:: python

    SHOPIT_PRODUCT_SERIALIZER_FIELDS = [
        'id', 'name', 'slug', 'caption', 'code', 'kind', 'url', 'add_to_cart_url', 'price', 'is_available',
    ]

Above is the default config, here's a list of all available fields:

.. code:: python

    ['id', 'name', 'slug', 'caption', 'code', 'kind', 'url', 'add_to_cart_url', 'price', 'is_available',
     'description', 'unit_price', 'discount', 'tax', 'availability', 'category', 'brand', 'manufacturer',
     'discountable', 'modifiers', 'flags', 'width', 'height', 'depth', 'weight', 'available_attributes',
     'group',  'attributes', 'published', 'quantity', 'order', 'active', 'created_at', 'updated_at',
     'is_single', 'is_group', 'is_variant', 'is_discounted', 'is_taxed',  'discount_percent', 'tax_percent',
     'discount_amount', 'tax_amount', 'variants', 'variations', 'attachments', 'relations', 'reviews']

A list of serializer fields for a product detail.

.. code:: python

    SHOPIT_PRODUCT_DETAIL_SERIALIZER_FIELDS = SHOPIT_PRODUCT_SERIALIZER_FIELDS + ['variants', 'attributes']

Template choices used when rendering an attribute.

.. code:: python

    SHOPIT_ATTRIBUTE_TEMPLATES = ()

Relation kind choices on a ``ProductRelation`` model.

.. code:: python

    SHOPIT_RELATION_KINDS = (
        ('up-sell', _('Up-sell')),
        ('cross-sell', _('Cross-sell')),
    )

Rating choices for product reviews.

.. code:: python

    SHOPIT_REVIEW_RATINGS = ()

Is review active by default when created.

.. code:: python

    SHOPIT_REVIEW_ACTIVE_DEFAULT = True

Modifier
========

A list of ``ModifierCondition`` classes that will be used as choices for conditions in a Modifier.

.. code:: python

    SHOPIT_MODIFIER_CONDITIONS = [
        'shopit.modifier_conditions.PriceGreaterThanCondition',
        'shopit.modifier_conditions.PriceLessThanCondition',
        'shopit.modifier_conditions.QuantityGreaterThanCondition',
        'shopit.modifier_conditions.QuantityLessThanCondition',
    ]

Text editor
===========

A text editor widget used to render a rich textarea in **Shopit**.

.. code:: python

    SHOPIT_TEXT_EDITOR = 'djangocms_text_ckeditor.widgets.TextEditorWidget'

Single apphook
==============

Load urls under a single ``ShopitApphook``, or leave the ability to add apps separately.

.. code:: python

    SHOPIT_SINGLE_APPHOOK = False

Filter attributes
=================

Designates if products of kind ``VARIANT`` should be included in attribute filtered results.

.. code:: python

    SHOPIT_FILTER_ATTRIBUTES_INCLUDES_VARIANTS = False

