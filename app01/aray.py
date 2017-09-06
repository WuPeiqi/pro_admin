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
            _change = QueryDict(mutable=True)
            _change['_change_filter'] = self.request.GET.urlencode()
            tpl = "<a href='{0}?{1}'>编辑</a>".format(edit_url, _change.urlencode())
            return mark_safe(tpl)

    # 页面上显示的字段
    list_display = (checkbox_field, 'username', 'pwd', 'fk', custom_field, edit_field)


v1.site.register(models.UserInfo,UserModelAdmin)
v1.site.register(models.UserGroup)
v1.site.register(models.Some)