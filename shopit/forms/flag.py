# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from mptt.forms import MPTTAdminForm
from parler.forms import TranslatableModelForm

from shopit.models.flag import Flag


class FlagModelForm(MPTTAdminForm, TranslatableModelForm):
    class Meta:
        model = Flag
        exclude = []
