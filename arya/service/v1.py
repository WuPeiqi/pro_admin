#!/usr/bin/env python
# -*- coding:utf-8 -*-
import urllib.parse
from django.shortcuts import render
from django.template.response import TemplateResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import six


class BaseAryaModal(object):
    def __init__(self, model_class, site):
        self.model_class = model_class
        self.app_label = model_class._meta.app_label
        self.model_name = model_class._meta.model_name

        self.site = site

    @property
    def changelist_url(self):
        # redirect_url = "%s?%s" % (reverse('%s:%s_%s' % (self.site.namespace, self.app_label, self.model_name)),
        #                           urllib.parse.urlencode(self.change_list_condition))
        redirect_url = "%s?%s" % (reverse('%s:%s_%s' % (self.site.namespace, self.app_label, self.model_name)),
                                  self.change_list_condition.urlencode())
        return redirect_url

    def another_urls(self):
        """
        钩子函数，用于自定义额外的URL
        :return: 
        """
        return []

    def get_urls(self):
        from django.conf.urls import url
        info = self.model_class._meta.app_label, self.model_class._meta.model_name

        urlpatterns = [
            url(r'^$', self.changelist_view, name='%s_%s_changelist' % info),
            url(r'^add/$', self.add_view, name='%s_%s_add' % info),
            url(r'^(.+)/delete/$', self.delete_view, name='%s_%s_delete' % info),
            url(r'^(.+)/change/$', self.change_view, name='%s_%s_change' % info),
            # For backwards compatibility (was the change url before 1.9)
            # url(r'^(.+)/$', RedirectView.as_view(pattern_name='%s:%s_%s_change' % ((self.backend_site.name,) + info))),
        ]
        urlpatterns += self.another_urls()
        return urlpatterns

    @property
    def urls(self):
        return self.get_urls()

    # ########## CURD功能 ##########

    # 定制列表页面模板
    change_list_template = []

    # 列表页面中默认的筛选条件
    change_list_condition = {}


    def get_model_field_name_list(self):
        """
        获取当前model中定义的字段
        :return: 
        """
        # print(type(self.model_class._meta))
        # from django.db.models.options import Options
        return [item.name for item in self.model_class._meta.fields]

    def get_all_model_field_name_list(self):
        """
        # 获取当前model中定义的字段（包括反向查找字段）
        :return: 
        """
        return [ item.name for item in self.model_class._meta._get_fields()]


    def get_change_list_condition(self):
        field_list = self.get_all_model_field_name_list()
        condition = {}
        for k in self.change_list_condition:
            if k not in field_list:
                break
            condition[k + "__in"] = self.change_list_condition.getlist(k)
        return condition

    def changelist_view(self, request):
        """
        显示数据列表
        :param request: 
        :return: 
        """
        self.change_list_condition = request.GET


        result_list = self.model_class.objects.filter(**self.get_change_list_condition())

        context = {
            'result_list': result_list
        }

        return TemplateResponse(request, self.change_list_template or [
            'arya/%s/%s/change_list.html' % (self.app_label, self.model_name),
            'arya/%s/change_list.html' % self.app_label,
            'arya/change_list.html'
        ], context)

    def add_view(self, request):
        """
        添加页面
        :param request: 
        :return: 
        """
        return TemplateResponse(request, self.change_list_template or [
            'arya/%s/%s/add.html' % (self.app_label, self.model_name),
            'arya/%s/add.html' % self.app_label,
            'arya/add.html'
        ])

    def delete_view(self, request, pk):
        """
        删除
        :param request: 
        :param pk: 
        :return: 
        """
        # 获取列表URL + 获取之前的保存筛选条件

        return redirect(self.changelist_url)

    def change_view(self, request, pk):
        """
        修改页面
        :param request: 
        :param pk: 
        :return: 
        """
        if request.method == 'GET':
            return TemplateResponse(request, self.change_list_template or [
                'arya/%s/%s/change.html' % (self.app_label, self.model_name),
                'arya/%s/change.html' % self.app_label,
                'arya/change.html'
            ])
        elif request.method == 'POST':

            # 如果修改成功，则跳转回去原来筛选页面
            return redirect(self.changelist_url)

        else:
            raise Exception('当前URL只支持GET/POST方法')


class AryaSite(object):
    def __init__(self, app_name='arya', namespace='arya'):
        self.app_name = app_name
        self.namespace = namespace
        self._registry = {}

    def register(self, model_class, arya_model_class=BaseAryaModal):
        self._registry[model_class] = arya_model_class(model_class, self)

    def get_urls(self):
        from django.conf.urls import url, include

        urlpatterns = [
            url(r'^$', self.index, name='index'),
            url(r'^login/$', self.login, name='login'),
            url(r'^logout/$', self.logout, name='logout'),
        ]

        for model_class, arya_model_obj in self._registry.items():
            urlpatterns += [
                url(r'^%s/%s/' % (model_class._meta.app_label, model_class._meta.model_name),
                    include(arya_model_obj.urls))
            ]
        return urlpatterns

    @property
    def urls(self):
        """
        创建URL对应关系
        :return: 元组类型：url关系列表或模块（模块内部必须有urlpatterns属性）；app_name；namespace
        """

        return self.get_urls(), self.app_name, self.namespace

    def login(self, request):
        """
        用户登录
        :param request: 
        :return: 
        """
        pass

    def logout(self, request):
        """
        用户注销
        :param request: 
        :return: 
        """
        pass

    def index(self, request):
        """
        首页
        :param request: 
        :return: 
        """
        pass


site = AryaSite()
