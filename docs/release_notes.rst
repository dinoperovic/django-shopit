Release notes
#############

Release notes for **Shopit**.

----

0.2.3
=====

* Handle NoReverseMatch for `add_to_cart_url` in a Product serializer.
* Add `order_insertion_by` to MPTT models.

0.2.2
=====

* Add filtering by modifiers.
* Update django-shop requirement to 0.10.2.

0.2.1
=====

* Fixes problem with migrations.

0.2.0
=====

* Add support for `Django 1.10` & `DjangoSHOP 0.10.x`.
* Alter templates to use Bootstrap 4 by default.
* Create example project, move tests.
* Rename description & caption fields to start with underscore.

.. attention::

    Requires ``python manage.py migrate shopit`` to add a product code to the CartItem, rename description & caption
    fields, as well as adding an additional setting
    ``SHOP_PRODUCT_SUMMARY_SERIALIZER = 'shopit.serializers.ProductSummarySerializer'``.

0.1.4
=====

* Add `description` field to categorization models.
* Move variant generator methods from admin to the model. Now ``create_all_variants`` and ``create_variant`` are
  available on the model.
* Update add to cart ``get_context`` to ensure correct product translation is returned.

.. attention::

    Requires ``python manage.py migrate shopit`` to create description field on categorization models.

0.1.3
=====

* Bugfixes.
* Fix ``get_object`` and ``get_queryset`` in product views returning inconsistant results.
* Add ``get_view_url`` to product detail view to return correct translated url.

0.1.2
=====

* Add price range filtering in ``get_products`` templatetag.
* Move product filtering to a manager.
* Allow mutiple flags to be passed to the ``get_products`` templatetag.
* Optimize attribute filtering with `prefetch_related`.
* Enable sorting the products.
* Don't fetch flags from categorization on a product. Categorization flags are used separately to mark categorization
  and the don't affect the products.
* Fix templatetags.
* Add option to limit ``get_categorization`` templatetag to a set of products.
* Enable filtering categorization and flags via querystring. Change price range querystrings.
* Add ``get_flags`` templatetag.
* Make `Flag` model an mptt model with a parent field.
* Show flags as filter_horizontal instead of CheckboxInput in product admin.
* Show localized amounts in product admin summary field.
* Use ``as_decimal`` when displaying price steps in template instead of floatformat.

.. attention::

    Requires ``python manage.py migrate shopit`` to create mptt fields on a Flag model.

0.1.1
=====

* Ensure customer is recognized before registering a new account. This works around an error
  **"Unable to proceed as guest without items in the cart"** when registering without a cart.
* Make fields in product serializer editable through settings, set optimized defaults.
* Fix error when mergin dictionaries in python3.
* Remove redundant code.
* Fix trying to generate image thumbnail on attachment when `file` is None.
* Fix weight setter setting width instead of weight.

0.1.0
=====

* Initial release.
