#!/usr/bin/env python
# -*- coding:utf-8 -*-

import re
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import HttpResponse
from django.utils.safestring import mark_safe


class RbacMiddleware(MiddlewareMixin):
    def process_request(self, request, *args, **kwargs):
        """
        检查用户是否具有权限访问当前URL
        :param request: 
        :param args: 
        :param kwargs: 
        :return: 
        """

        """跳过无需权限访问的URL"""
        for pattern in settings.RBAC_NO_AUTH_URL:
            if re.match(pattern, request.path_info):
                return None

        """获取当前用户session中的权限信息"""
        permission_url_list = request.session.get(settings.RBAC_PERMISSION_URL_SESSION_KEY)
        if not permission_url_list:
            return HttpResponse(settings.RBAC_PERMISSION_MSG)

        """当前URL和session中的权限进行匹配"""
        flag = False
        for url in permission_url_list:
            pattern = settings.RBAC_MATCH_PARTTERN.format(url)
            if re.match(pattern, request.path_info):
                flag = True
                break

        if not flag:
            if settings.DEBUG:
                return HttpResponse("无权访问，你的权限有：<br/>" + mark_safe("<br/>".join(permission_url_list)))
            else:
                return HttpResponse(settings.RBAC_PERMISSION_MSG)
