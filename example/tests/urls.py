# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.conf.urls import include, url
from django.conf.urls.i18n import i18n_patterns

urlpatterns = i18n_patterns(
    url(r'^shopit/', include('shopit.urls')),
)
