# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import OrderedDict
from urllib.parse import urljoin

from django.conf import settings
from rest_framework.pagination import LimitOffsetPagination, PageNumberPagination
from rest_framework.response import Response
from rest_framework.utils.urls import replace_query_param, remove_query_param


class CustomLimitOffsetPagination(LimitOffsetPagination, PageNumberPagination):
    def get_next_link(self):

        if self.offset + self.limit >= self.count:
            return None

        url = hasattr(settings, 'ROOT_URL') and urljoin(
            settings.ROOT_URL, self.request.get_full_path()) or self.request.build_absolute_uri()
        url = replace_query_param(url, self.limit_query_param, self.limit)

        offset = self.offset + self.limit
        return replace_query_param(url, self.offset_query_param, offset)

    def get_previous_link(self):

        if self.offset <= 0:
            return None

        url = hasattr(settings, 'ROOT_URL') and urljoin(
            settings.ROOT_URL, self.request.get_full_path()) or self.request.build_absolute_uri()
        url = replace_query_param(url, self.limit_query_param, self.limit)

        if self.offset - self.limit <= 0:
            return remove_query_param(url, self.offset_query_param)

        offset = self.offset - self.limit
        return replace_query_param(url, self.offset_query_param, offset)


class CommonPagination(CustomLimitOffsetPagination):
    '''
    分页设置
    '''
    page_size = 20
    page_size_query_param = 'size'

    def get_paginated_response(self, data):
        return Response(
            OrderedDict([('count', self.count), ('next', self.get_next_link()),
                         ('previous', self.get_previous_link()), ('results', data),
                         ('size', self.limit)]))
