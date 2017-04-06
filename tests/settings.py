# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


SECRET_KEY = 'secret'

SITE_ID = 1

ROOT_URLCONF = 'tests.urls'

# Application definition
INSTALLED_APPS = [
    'django.contrib.auth',
    'email_auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',

    # django-cms
    'cms',
    'menus',
    'treebeard',
    'easy_thumbnails',
    'filer',
    'djangocms_text_ckeditor',

    # django-shop
    'cmsplugin_cascade',
    'adminsortable2',
    'post_office',
    'shop',

    # shopit
    'parler',
    'shopit',
]


MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}


FIXTURE_DIRS = [os.path.join(BASE_DIR, 'tests', 'fixtures')]


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
            ],
        },
    },
]


CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}


PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']


# Internationalization
LANGUAGE_CODE = 'en'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True
LANGUAGES = [
    ('en', 'English'),
    ('hr', 'Hrvatski'),
]


# auth
AUTH_USER_MODEL = 'email_auth.User'


# cmsplugin_casced
CMSPLUGIN_CASCADE = {}


# shop
SHOP_APP_LABEL = 'shopit'
