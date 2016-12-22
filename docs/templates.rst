Templates
#########

You can use django-cms_ cascade plugins provided by django-shop_ to generate your cart, watch, checkout, account &
catalog pages. But if don't want to add the plugins yourself, **Shopit** comes with prebuild html templates for those
pages. Barebones and with simple jQuery implementation of front-end actions for you to easily override.
This will help you have a clean & simple starting boilerplate to build apon.

----

Account
=======

Account templates are located in ``templates/shopit/account/*`` and consist of:

* ``account_detail.html``
* ``account_login.html``
* ``account_order_detail.html``
* ``account_order_list.html``
* ``account_register.html``
* ``account_reset.html``
* ``account_reset_confirm.html``
* ``account_settings.html``

Catalog
=======

Catalog templates are located in ``templates/shopit/catalog/*`` and consist of:

* ``categorization_detail.html``
* ``categorization_list.html``
* ``product_detail.html``
* ``product_list.html``

There are general categorization templates that handle all categorization views by default. Categorization objects and
lists are passed into context as ``categorization`` and ``categorization_list`` as well as an actual model name
representation, for example **Category** views will also have ``category`` and ``category_list`` accessible.
You can also create a template for a specific categorization by using it's model name. For eg. for **Brand** model
you can create ``brand_detail.html`` and ``brand_list.html``.

Shop
====

Shop templates are located in ``templates/shopit/shop/*`` and consist of:

* ``cart.html``
* ``checkout.html``
* ``thanks.html``
* ``watch.html``

Templatetags
============

To use the **Shopit** templatetags library. Put ``{% load shopit_tags %}`` in your templates.

Filters
-------

.. code:: html

    # Cast a number to a Money format.
    {{ number|moneyformat }}

Simple tags
-----------

.. code:: django

    # Update the querystring maintaining the existant keys.
    {% query_transform color 'black' size='XL' %}

    # Fetch a set of products.
    {% get_products 3 flags='featured,awesome' category=3 brand=3 manufactured=3 as products %}

    # Fetch a set of categorization objects.
    {% get_categorization 'category' limit=3 level=1 depth=2 as categories %}
    {% get_categorization 'brand' limit=3 level=1 depth=2 as brands %}
    {% get_categorization 'manufacturer' products=product_list limit=3 level=1 depth=2 as manufacturers %}

    # Fetch a single flag, or a set of flags.
    {% get_flags 'featured' as featured_flag %}
    {% get_flags products=product_list level=1 parent='featured' as featured_flags %}

    # Fetch attributes for the set of products.
    {% get_attributes product as attributes %}

    # Get min and max price with the steps in between for a set of products.
    {% get_price_steps 3 product as price_steps %}


Inclusion tags
--------------

These are the templates to be included with inclusion tags. They are located
in ``templates/shopit/includes/*`` and consist of:

* ``add_to_cart.html``
* ``cart.html``
* ``order.html``

To include the templates you can write the following:

.. code:: html

    # Show add to cart button for the 'product' in context.
    {% add_to_cart %}

    # Show add to cart button for specified product with watch button included.
    {% add_to_cart product watch=True %}

    # Show editable cart.
    {% cart %}

    # Show static cart.
    {% cart editable=False %}

    # Show latest order.
    {% order %}

    # show specific order.
    {% order instance %}


.. _django-cms: https://github.com/divio/django-cms
.. _django-shop: https://github.com/awesto/django-shop
