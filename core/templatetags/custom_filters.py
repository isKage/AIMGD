from django import template
from itertools import zip_longest
from django.utils.safestring import mark_safe
import markdown as md

register = template.Library()


@register.filter
def zip(value1, value2):
    return zip_longest(value1, value2, fillvalue=None)


# @register.filter(name='markdown')  # 明确指定过滤器名称
# def markdown(value):
#     return md.markdown(value)

@register.filter
def markdown(value):
    """将markdown文本转换为安全的HTML"""
    if value:
        return mark_safe(md.markdown(value))
    return ""
