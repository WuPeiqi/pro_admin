#!/usr/bin/env python
# -*- coding:utf-8 -*-
import copy
import json
import urllib.parse
from django.template.response import TemplateResponse, SimpleTemplateResponse
from django.shortcuts import redirect,render,HttpResponse
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.http.request import QueryDict
from django.forms import Form, ModelForm
from django.forms import fields
from django.forms import widgets
from django.db.models import ForeignKey, ManyToManyField
from arya.utils.pagination import Page
from types import FunctionType

from django.http.request import QueryDict


def model_to_dict(instance, fields=None, exclude=None):
    from itertools import chain
    """
    Returns a dict containing the data in ``instance`` suitable for passing as
    a Form's ``initial`` keyword argument.

    ``fields`` is an optional list of field names. If provided, only the named
    fields will be included in the returned dict.

    ``exclude`` is an optional list of field names. If provided, the named
    fields will be excluded from the returned dict, even if they are listed in
    the ``fields`` argument.
    """
    opts = instance._meta
    data = {}
    for f in chain(opts.concrete_fields, opts.private_fields, opts.many_to_many):
        print(f, type(f))
        if not getattr(f, 'editable', False):
            continue
        if fields and f.name not in fields:
            continue
        if exclude and f.name in exclude:
            continue
        if type(f) == ForeignKey:
            data[f.name + "_id"] = f.value_from_object(instance)
        else:
            data[f.name] = f.value_from_object(instance)
    return data


class FilterList(object):
    """
    组合搜索项
    """

    def __init__(self, option, change_list, data_list, param_dict=None):
        self.option = option

        self.data_list = data_list

        self.param_dict = copy.deepcopy(param_dict)

        self.param_dict._mutable = True

        self.change_list = change_list

    def __iter__(self):

        base_url = self.change_list.arya_modal.changelist_url()
        tpl = "<a href='{0}' class='{1}'>{2}</a>"
        # 全部
        if self.option.name in self.param_dict:
            pop_value = self.param_dict.pop(self.option.name)
            url = "{0}?{1}".format(base_url, self.param_dict.urlencode())
            val = tpl.format(url, '', '全部')
            self.param_dict.setlist(self.option.name, pop_value)
        else:
            url = "{0}?{1}".format(base_url, self.param_dict.urlencode())
            val = tpl.format(url, 'active', '全部')
        yield mark_safe("<div class='whole'>")
        yield mark_safe(val)
        yield mark_safe("</div>")

        yield mark_safe("<div class='others'>")
        for obj in self.data_list:
            param_dict = copy.deepcopy(self.param_dict)

            pk = getattr(obj, self.option.val_func_name)() if self.option.val_func_name else obj.pk
            pk = str(pk)

            text = getattr(obj, self.option.text_func_name)() if self.option.text_func_name else str(obj)

            exist = False
            if pk in param_dict.getlist(self.option.name):
                exist = True

            if self.option.is_multi:
                if exist:
                    param_dict.getlist(self.option.name).remove(pk)
                else:
                    param_dict.appendlist(self.option.name, pk)
            else:
                param_dict[self.option.name] = pk
            url = "{0}?{1}".format(base_url, param_dict.urlencode())
            val = tpl.format(url, 'active' if exist else '', text)
            yield mark_safe(val)
        yield mark_safe("</div>")


class FilterOption(object):
    def __init__(self, field_or_func, is_multi=False, text_func_name=None, val_func_name=None):
        """
        :param field: 字段名称或函数
        :param is_multi: 是否支持多选
        :param text_func_name: 在Model中定义函数，显示文本名称，默认使用 str(对象)
        :param val_func_name:  在Model中定义函数，显示文本名称，默认使用 对象.pk
        """
        self.field_or_func = field_or_func
        self.is_multi = is_multi
        self.text_func_name = text_func_name
        self.val_func_name = val_func_name

    @property
    def is_func(self):
        if isinstance(self.field_or_func, FunctionType):
            return True

    @property
    def name(self):
        if self.is_func:
            return self.field_or_func.__name__
        else:
            return self.field_or_func


class ChangeList(object):
    def __init__(self, request, arya_modal, list_display, result_list, model_cls, list_filter, actions):
        self.request = request
        self.list_display = list_display
        self.list_filter = list_filter

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

        tpl = "<a class='btn btn-success' style='float:right' href='{0}?{1}'><span class='glyphicon glyphicon-share-alt' aria-hidden='true'></span> 新建数据</a>".format(
            add_url,
            _change.urlencode())
        return mark_safe(tpl)

    def gen_list_filter(self):

        for option in self.list_filter:
            if option.is_func:
                data_list = option.field_or_func(self)
            else:
                _field = self.model_cls._meta.get_field(option.field_or_func)
                if isinstance(_field, ForeignKey):
                    data_list = FilterList(option, self, _field.rel.model.objects.all(), self.request.GET)
                elif isinstance(_field, ManyToManyField):
                    data_list = FilterList(option, self, _field.rel.model.objects.all(), self.request.GET)
                else:
                    data_list = FilterList(option, self, _field.model.objects.all(), self.request.GET)
            yield data_list


class BaseAryaModal(object):
    def __init__(self, model_class, site):
        self.model_class = model_class
        self.app_label = model_class._meta.app_label
        self.model_name = model_class._meta.model_name

        self.site = site

        self.request = None

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
            url(r'^(.+)/detail/$', self.detail_view, name='%s_%s_detail' % info),
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
    add_form_template = []
    detail_template = []
    change_form_template = []

    """2. 定制列表中的筛选条件"""

    def get_model_field_name_list(self):
        """
        获取当前model中定义的字段
        :return: 
        """
        # print(type(self.model_class._meta))
        from django.db.models.options import Options
        return [item.name for item in self.model_class._meta.fields]

    def get_model_field_name_list_m2m(self):
        return [item.name for item in self.model_class._meta.many_to_many]

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

    list_display = "__str__"

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
    page_model_form = None

    @property
    def get_model_form_cls(self):
        model_form_cls = self.page_model_form
        if not model_form_cls:
            _meta = type('Meta', (object,), {'model': self.model_class, "fields": "__all__"})
            model_form_cls = type('DynamicModelForm', (ModelForm,), {'Meta': _meta})
        return model_form_cls

    """6. 定制查询组合条件"""
    list_filter = []

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
        self.request = request
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

        change_list = ChangeList(request, self, self.list_display, result_list, self.model_class, self.list_filter,
                                 actions=self.actions)
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

        if request.method == 'GET':
            form = self.get_model_form_cls()

        elif request.method == "POST":
            form = self.get_model_form_cls(data=request.POST, files=request.FILES)
            if form.is_valid():
                obj = form.save()
                popup_id = request.GET.get("_popup")
                if popup_id:
                    context = {'pk': obj.pk, 'value': str(obj), 'popup_id': popup_id}
                    return SimpleTemplateResponse('arya/popup_response.html',
                                                  {"popup_response_data": json.dumps(context)})
                else:
                    _change_filter = request.GET.get('_change_filter')
                    if _change_filter:
                        change_list_url = "{0}?{1}".format(self.changelist_url(), _change_filter)
                    else:
                        change_list_url = self.changelist_url()
                    return redirect(change_list_url)
        else:
            raise Exception('当前URL只支持GET/POST方法')
        context = {
            'form': form
        }
        return TemplateResponse(request, self.add_form_template or [
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
        self.model_class.objects.filter(pk=pk).delete()
        _change_filter = request.GET.get('_change_filter')
        if _change_filter:
            change_list_url = "{0}?{1}".format(self.changelist_url(), _change_filter)
        else:
            change_list_url = self.changelist_url()
        return redirect(change_list_url)

    def change_view(self, request, pk):
        """
        修改页面
        :param request: 
        :param pk: 
        :return: 
        """
        obj = self.model_class.objects.filter(pk=pk).first()
        if request.method == 'GET':
            form = self.get_model_form_cls(instance=obj)
        elif request.method == 'POST':
            form = self.get_model_form_cls(data=request.POST, files=request.FILES, instance=obj)
            if form.is_valid():
                form.save()
                # 如果修改成功，则跳转回去原来筛选页面
                _change_filter = request.GET.get('_change_filter')
                if _change_filter:
                    change_list_url = "{0}?{1}".format(self.changelist_url(), _change_filter)
                else:
                    change_list_url = self.changelist_url()
                return redirect(change_list_url)
        else:
            raise Exception('当前URL只支持GET/POST方法')

        context = {
            'form': form
        }
        return TemplateResponse(request, self.change_form_template or [
            'arya/%s/%s/change.html' % (self.app_label, self.model_name),
            'arya/%s/change.html' % self.app_label,
            'arya/change.html'
        ], context)

    def detail_view(self, request, pk):
        """
        查看详细
        :param request: 
        :param pk: 
        :return: 
        """
        row = self.model_class.objects.filter(pk=pk).first()
        fields = self.get_model_form_cls.Meta.fields
        if fields == '__all__':
            fields = self.get_model_field_name_list()
            # print(self.get_model_field_name_list_m2m())
        for name in fields:
            val = getattr(row, name)
            # print(name, val)

        context = {
            'row': row
        }
        return TemplateResponse(request, self.change_form_template or [
            'arya/%s/%s/detail.html' % (self.app_label, self.model_name),
            'arya/%s/detail.html' % self.app_label,
            'arya/detail.html'
        ], context)


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
        from arya import models
        from arya.service import rbac
        obj = models.User.objects.get(id=1)
        # 初始化权限信息
        rbac.initial_permission(request, obj)

        return HttpResponse('Login')

        # if request.method == 'GET':
        #     return render(request,'login.html')
        # else:
        #     from arya import models
        #     from arya.service import rbac
        #
        #     user = request.POST.get('username')
        #     pwd = request.POST.get('password')
        #     obj = models.User.objects.filter(username=user,password=pwd).first()
        #
        #     rbac.initial_permission(request,obj)
        #     return redirect('/')

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
        return render(request,'index.html')


site = AryaSite()
