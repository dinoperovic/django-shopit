# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from shopit.conf import app_settings


def get_error_message(key, default=""):
    """
    Returns error message from Shopit's `ERROR_MESSAGES` setting.
    """
    return getattr(app_settings.ERROR_MESSAGES, key, default)
