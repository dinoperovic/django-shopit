Release notes
#############

Release notes for **Shopit**.

----

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
