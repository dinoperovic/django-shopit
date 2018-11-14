Getting started
###############

Get started with installing and configuring **Shopit**.

----

Requirements
============

* Django_ 1.10, 1.9
* django-shop_ as shop framework.
* django-cms_ for placeholders.
* django-parler_ to translate everything.
* django-mptt_ for tree management.
* django-admin-sortable2_ to sort stuff.
* django-measurement_ to add measurements.
* django-phonenumber-field_ for customer's phone number.

Installation
============

Install using **pip**:

.. code:: bash

    pip install django-shopit

You should follow django-cms_ & django-shop_ installation guide first, and then add the following to your settings:

.. code:: python

    INSTALLED_APPS = [
        ...
        'adminsortable2',
        'mptt',
        'parler',
        'shopit',
    ]

    SHOP_APP_LABEL = 'shopit'
    SHOP_PRODUCT_SUMMARY_SERIALIZER = 'shopit.serializers.ProductSummarySerializer'
    SHOP_CART_MODIFIERS = (
        'shop.modifiers.DefaultCartModifier',
        'shopit.modifiers.ShopitCartModifier',
        ...
    )

Urls
----

There are two ways to configure the urls. First would be to add to your ``urls.py``:

.. code:: python

    urlpatterns = [
        url(r'^shop/', include('shopit.urls')),
        ...
    ]

The second option is to use django-cms_ apphooks. **Shopit** comes with a couple of those for different application parts. ``ShopitApphook`` is the main one, and one that should always be attached to a page (if the urls are not already added). Then there are other optional apphooks for *account*, *categorization* & *products*. If you want to keep it simple, and not have to set every application part individually. You can add to your settings:

.. code:: python

    SHOPIT_SINGLE_APPHOOK = True

This will load all the neccesary urls under the ``ShopitApphook``.


.. _Django: https://www.djangoproject.com/
.. _django-shop: https://github.com/awesto/django-shop
.. _django-cms: https://github.com/divio/django-cms
.. _django-parler: https://github.com/django-parler/django-parler
.. _django-mptt: https://github.com/django-mptt/django-mptt
.. _django-admin-sortable2: https://github.com/jrief/django-admin-sortable2
.. _django-measurement: https://github.com/coddingtonbear/django-measurement
.. _django-phonenumber-field: https://github.com/stefanfoulis/django-phonenumber-field
