# Shopit

[![Build Status](https://img.shields.io/travis/dinoperovic/djangoshop-shopit.svg)](https://travis-ci.org/dinoperovic/djangoshop-shopit)
[![Codecov](https://img.shields.io/codecov/c/github/dinoperovic/djangoshop-shopit.svg)](http://codecov.io/github/dinoperovic/djangoshop-shopit)
[![PyPI version](https://img.shields.io/pypi/v/djangoshop-shopit.svg)](https://pypi.python.org/pypi/djangoshop-shopit)

**A fully featured shop application built on [djangoSHOP](http://www.django-shop.org) framework.**

This project aims to provide a **quick & easy** way to set up a fully featured shop without much hassle.

---

## Features

Shopit comes with the most useful features that a classic shops needs, out of the box.

Here's what you can expect:

* Easily manage **Products** and their variations with custom **Attributes**.
* **Attach** images, videos & files on products.
* Set *Up-sell*, *Cross-sell* and other customized **Relations** between products.
* Create custom checkbox **Flags** for products and categorization.
* Group products in **Category**, **Brand** and **Manufacturer** groups.
* Create discounts and promotional codes with **Modifiers**.
* Add custom **Taxes** for categories and products.
* Enable customer **Reviews** on products.

## Requirements

* [Django] 1.11, 1.10
* [django-shop] as shop framework.
* [django-cms] for placeholders.
* [django-parler] to translate everything.
* [django-mptt] for tree management.
* [django-admin-sortable2] to sort stuff.
* [django-measurement] to add measurements.
* [django-phonenumber-field] for customer's phone number.

## Installation

Install using *pip*:

```bash
pip install djangoshop-shopit
```

You should follow [django-cms] & [django-shop] installation guide first, and then add the following to your settings:

```python
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
```

#### Urls

There are two ways to configure the urls. First would be to add to your `urls.py`:

```python
urlpatterns = [
    url(r'^shop/', include('shopit.urls')),
    ...
]
```

The second option is to use [django-cms] apphooks. **Shopit** comes with a couple of those for different application parts. `ShopitApphook` is the main one, and one that should always be attached to a page (if the urls are not already added). Then there are other optional apphooks for *account*, *categorization* & *products*. If you want to keep it simple, and not have to set every application part individually. You can add to your settings:

```python
SHOPIT_SINGLE_APPHOOK = True
```

This will load all the neccesary urls under the `ShopitApphook`.

## Documentation

Full documentation is availiable on [ReadTheDocs](http://djangoshop-shopit.readthedocs.org).


[Django]: https://www.djangoproject.com/
[django-shop]: https://github.com/awesto/django-shop
[django-cms]: https://github.com/divio/django-cms
[django-parler]: https://github.com/django-parler/django-parler
[django-mptt]: https://github.com/django-mptt/django-mptt
[django-admin-sortable2]: https://github.com/jrief/django-admin-sortable2
[django-measurement]: https://github.com/coddingtonbear/django-measurement
[django-phonenumber-field]: https://github.com/stefanfoulis/django-phonenumber-field
