Release notes
#############

Release notes for **Shopit**.

----

0.1.2
=====

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
