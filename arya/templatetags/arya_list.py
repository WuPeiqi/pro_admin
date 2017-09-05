#!/usr/bin/env python
# -*- coding:utf-8 -*-
from django.template import Library
from django.db.models import ForeignKey
from django.db.models import ManyToManyField
from types import FunctionType

register = Library()


def result_header_list(change_list):
    """
    处理表格头部
    :param modal_cls: 
    :param list_display: 
    :return: 
    """
    for name in change_list.list_display:
        yield name(change_list.arya_modal,is_header=True) if isinstance(name, FunctionType) else change_list.model_cls._meta.get_field(name).verbose_name


def result_body_list(change_list):
    """
    处理表格内容
    :param queryset: 
    :param list_display: 
    :return: 
    """
    for row in change_list.result_list:
        yield [name(change_list.arya_modal,obj=row) if isinstance(name, FunctionType) else getattr(row, name) for name in change_list.list_display]


@register.inclusion_tag('arya/change_list_results.html')
def show_result_list(change_list):
    """
    展示数据表格
    1. 表头
    2. 表体
    :param list_display: 
    :param queryset: 
    :return: 
    """

    return {
        'result': result_body_list(change_list),
        'headers': result_header_list(change_list)
    }
