#!/usr/bin/env python
# -*- coding:utf-8 -*-
import urllib.parse
from django.shortcuts import render
from django.template.response import TemplateResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import six
from django.utils.safestring import mark_safe
from django.http.request import QueryDict
from django.forms import Form
from django.forms import fields
from django.forms import widgets
from arya.utils.pagination import Page

import copy


class ChangeList(object):
    def __init__(self, request, arya_modal, list_display, result_list, model_cls, actions):
        self.request = request
        self.list_display = list_display

        self.model_cls = model_cls
        self.arya_modal = arya_modal
        self.actions = actions

        all_count = result_list.count()
        query_params = copy.copy(request.GET)
        query_params._mutable = True

        self.pager = Page(self.request.GET.get('page'), all_count, base_url=self.arya_modal.changelist_url(),
                          query_params=query_params)
        self.result_list = result_list[self.pager.start:self.pager.end]

    def add_btn(self):
        """
        列表页面定制新建数据按钮
        :return: 
        """
        add_url = reverse(
            '%s:%s_%s_add' % (self.arya_modal.site.namespace, self.arya_modal.app_label, self.arya_modal.model_name))

        _change = QueryDict(mutable=True)
        _change['_change_filter'] = self.request.GET.urlencode()

        tpl = "<a class='btn btn-success' style='float:right' href='{0}?{1}'>新建数据</a>".format(add_url,
                                                                                              _change.urlencode())
        return mark_safe(tpl)


class PageForm(Form):
    user = fields.CharField(
        label='用户名',
        label_suffix=':',
        widget=widgets.TextInput(attrs={'class': 'form-control'})
    )
    pwd = fields.CharField(
        label='密码',
        label_suffix=':',
        widget=widgets.TextInput(attrs={'class': 'form-control'})
    )
    email = fields.EmailField(
        label='邮箱',
        label_suffix=':',
        widget=widgets.TextInput(attrs={'class': 'form-control'})
    )


class BaseAryaModal(object):
    def __init__(self, model_class, site):
        self.model_class = model_class
        self.app_label = model_class._meta.app_label
        self.model_name = model_class._meta.model_name

        self.site = site

    def changelist_param_url(self, query_params):
        # redirect_url = "%s?%s" % (reverse('%s:%s_%s' % (self.site.namespace, self.app_label, self.model_name)),
        #                           urllib.parse.urlencode(self.change_list_condition))
        redirect_url = "%s?%s" % (
            reverse('%s:%s_%s_changelist' % (self.site.namespace, self.app_label, self.model_name)),
            query_params.urlencode())
        return redirect_url

    def changelist_url(self):
        redirect_url = reverse('%s:%s_%s_changelist' % (self.site.namespace, self.app_label, self.model_name))
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

    """1. 定制显示列表的Html模板"""
    change_list_template = []

    """2. 定制列表中的筛选条件"""

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
        return [item.name for item in self.model_class._meta._get_fields()]

    def get_change_list_condition(self, query_params):

        field_list = self.get_all_model_field_name_list()
        condition = {}
        for k in query_params:
            if k not in field_list:
                # raise Exception('条件查询字段%s不合法，合法字段为：%s' % (k, ",".join(field_list)))
                continue
            condition[k + "__in"] = query_params.getlist(k)
        return condition

    """3. 定制数据列表开始"""

    def checkbox_field(self, obj=None, is_header=False):
        if is_header:
            tpl = "<input type='checkbox' id='headCheckBox' />"
            return mark_safe(tpl)
        else:
            tpl = "<input type='checkbox' name='pk' value='{0}' />".format(obj.pk)
            return mark_safe(tpl)

    def custom_field(self, obj=None, is_header=False):
        if is_header:
            return '自定义列名称'
        else:
            return obj.username

    def edit_field(self, obj=None, is_header=False):
        if is_header:
            return '操作'
        else:
            edit_url = reverse('{0}:{1}_{2}_change'.format(self.site.namespace, self.app_label, self.model_name),
                               args=(obj.pk,))
            tpl = "<a href='{0}'>编辑</a>".format(edit_url)
            return mark_safe(tpl)

    # 页面上显示的字段
    list_display = (checkbox_field, 'username', 'pwd', 'fk', custom_field, edit_field)

    """4. 定制Action行为"""

    def delete_action(self, request, queryset):
        """
        定制Action行为
        :param request: 
        :param queryset: 
        :return: True表示保留所有条件,False表示回到列表页面
        """
        pk_list = request.POST.getlist('pk')
        queryset.filter(id__in=pk_list).delete()

        return True

    delete_action.short_description = "删除选择项"
    actions = [delete_action, ]

    """5. 定制添加和编辑页面中的Form组件"""
    page_form = PageForm

    """增删改查方法"""

    def changelist_view(self, request):
        """
        显示数据列表
        1. 数据列表
        2. 筛选
        3. 分页
        4. 是否可编辑
        5. 搜索
        6. 定制行为
        :param request: 
        :return: 
        """

        result_list = self.model_class.objects.filter(**self.get_change_list_condition(request.GET))

        if request.method == "POST":
            """执行Action行为"""
            action = request.POST.get('action')
            if not action:
                return redirect(self.changelist_param_url(request.GET))
            if getattr(self, action)(request, result_list):
                return redirect(self.changelist_param_url(request.GET))
            else:
                return redirect(self.changelist_url())

        change_list = ChangeList(request, self, self.list_display, result_list, self.model_class, actions=self.actions)
        context = {
            'cl': change_list,

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
        from django.forms.boundfield import BoundField
        print(request.GET)
        if request.method == 'GET':
            # 创建Form表单
            form = self.page_form()
        else:
            form = self.page_form(data=request.POST, files=request.FILES)
            if form.is_valid():
                print(form.cleaned_data)
                # self.model_class.objects.create(**form.cleaned_data)
                _change_filter = request.GET.get('_change_filter')
                if _change_filter:
                    change_list_url = "{0}?{1}".format(self.changelist_url(), _change_filter)
                else:
                    change_list_url = self.changelist_url()
                return redirect(change_list_url)
            else:
                print(form.errors)
        context = {
            'form': form
        }
        return TemplateResponse(request, self.change_list_template or [
            'arya/%s/%s/add.html' % (self.app_label, self.model_name),
            'arya/%s/add.html' % self.app_label,
            'arya/add.html'
        ], context)

    def delete_view(self, request, pk):
        """
        删除
        :param request: 
        :param pk: 
        :return: 
        """
        # 获取列表URL + 获取之前的保存筛选条件
        return redirect(self.changelist_param_url(request.GET))

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
            return redirect(self.changelist_url())

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
