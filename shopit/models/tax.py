# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from parler.models import TranslatableModel, TranslatedFields


@python_2_unicode_compatible
class Tax(TranslatableModel):
    translations = TranslatedFields(
        name=models.CharField(
            _('Name'),
            max_length=128,
        ),
    )

    percent = models.DecimalField(
        _('Percent'),
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_('Tax percentage.'),
    )

    order = models.PositiveIntegerField(
        _('Sort'),
        default=0,
    )

    class Meta:
        db_table = 'shopit_taxes'
        verbose_name = _('Tax')
        verbose_name_plural = _('Taxes')
        ordering = ['order']

    def __str__(self):
        return self.safe_translation_getter('name', any_language=True)
