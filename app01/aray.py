from django.urls import reverse
from django.utils import six
from django.utils.safestring import mark_safe
from django.http.request import QueryDict
from arya.service import v1
from . import models


class UserModelAdmin(v1.BaseAryaModal):
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
            del_url = reverse('{0}:{1}_{2}_delete'.format(self.site.namespace, self.app_label, self.model_name),
                              args=(obj.pk,))
            detail_url = reverse('{0}:{1}_{2}_detail'.format(self.site.namespace, self.app_label, self.model_name),
                                 args=(obj.pk,))

            param_url = ""
            if len(self.request.GET):
                _change = QueryDict(mutable=True)
                _change['_change_filter'] = self.request.GET.urlencode()
                param_url = "?{0}".format(_change.urlencode())

            tpl = "<a href='{0}{3}'>编辑</a> | <a href='{1}{3}'>删除</a> | <a href='{2}{3}'>查看详细</a>".format(edit_url,
                                                                                                         del_url,
                                                                                                         detail_url,
                                                                                                         param_url)
            return mark_safe(tpl)

    # 页面上显示的字段
    list_display = (checkbox_field, 'username', 'pwd', 'fk', custom_field, edit_field)

    list_filter = [
        v1.FilterOption('username', False,text_func_name="arya_filter_name_text", val_func_name="arya_filter_name_value"),
        v1.FilterOption('fk', True),
        v1.FilterOption('mm', False, text_func_name="arya_filter_mm_text", val_func_name="arya_filter_mm_value"),
    ]
    """
    用于在创建组合搜索
        1. 搜索元素必须是FilterOption对象
        2. FilterOption参数：
                - :param field: 字段名称或函数
                - :param is_multi: 是否支持多选
                - :param text_func_name: 在Model中定义函数，显示文本名称，默认使用 str(对象)
                - :param val_func_name:  在Model中定义函数，显示文本名称，默认使用 对象.pk
        示例一：
             
                list_filter = [
                    v1.FilterOption('username', False),
                    v1.FilterOption('fk', False),
                    v1.FilterOption('mm', False),
                ]
                
        示例二：
                list_filter = [
                    v1.FilterOption('username', False,text_func_name=arya_filter_fk_text,value_func_name=arya_filter_fk_name),
                    v1.FilterOption('fk', False),
                    v1.FilterOption('mm', False),
                ]
                
                class UserInfo(models.Model):
                    username = models.CharField(verbose_name='用户名',max_length=32)
                    pwd = models.CharField(verbose_name='密码',max_length=32)
                    fk = models.ForeignKey(verbose_name='用户组',to=UserGroup,null=True)
                    mm = models.ManyToManyField(verbose_name='选多个',to=Some)
                
                    def arya_filter_fk_text(self):
                        return self.username
                    
                    def arya_filter_fk_name(self):
                        return self.username
                    
        示例三：
                def custom():
                    data_list = models.XX.objects.all()
                    return data_list
                    
                    
                list_filter = [
                    v1.FilterOption('username'),
                    v1.FilterOption(custom, False),
                ]
        示例四：
                def custom():
                    data_list = models.XX.objects.all()
                    return data_list
                    
                    
                list_filter = [
                    v1.FilterOption('username'),
                    v1.FilterOption(custom, False，text_func_name=arya_filter_nnn_text,value_func_name=arya_filter_nnn_name),
                ]
                
                class XX(models.Model):
                    ... = models.CharField(verbose_name='用户名',max_length=32)
                
                    def arya_filter_nnn_text(self):
                        return self.username
                    
                    def arya_filter_nnn_name(self):
                        return self.username
            
    """
    #
    # 如果是自定义字段
    # 示例：


v1.site.register(models.UserInfo, UserModelAdmin)
v1.site.register(models.UserGroup)
v1.site.register(models.Some)
