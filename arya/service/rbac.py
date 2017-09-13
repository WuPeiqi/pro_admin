#!/usr/bin/env python
# -*- coding:utf-8 -*-
import re
from django.conf import settings
from .. import models


def initial_permission(request, user):
    """
    初始化权限，获取当前用户权限并添加到session中
    
    :param request: 请求对象
    :param user: 当前用户对象
    :return: 
    """
    # 1.获取当前用户所有角色 user.roles.all()
    # roles = user.roles.all()

    # 2.获取角色对应的所有权限
    permission_list = user.roles.values('permissions__id', 'permissions__caption', 'permissions__url',
                                        'permissions__menu_id').distinct()

    permission_url_list = []
    permission_menu_list = []
    for item in permission_list:
        permission_url_list.append(item['permissions__url'])
        if item['permissions__menu_id']:
            permission_menu_list.append(item)

    # 3. 权限写入session
    request.session[settings.RBAC_PERMISSION_URL_SESSION_KEY] = permission_url_list

    # 4. 菜单写入session
    menu_list = list(models.Menu.objects.values('id', 'caption', 'parent_id'))
    request.session[settings.RBAC_MENU_PERMISSION_SESSION_KEY] = {
        settings.RBAC_MENU_KEY: menu_list,
        settings.RBAC_MENU_PERMISSION_KEY: permission_menu_list
    }
