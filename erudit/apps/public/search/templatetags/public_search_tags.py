# -*- coding: utf-8 -*-

from django import template
from django.utils.html import mark_safe

register = template.Library()


@register.filter
def highlight(text, word):
    return mark_safe(text.replace(word, '<mark class="highlight">{}</mark>'.format(word)))
