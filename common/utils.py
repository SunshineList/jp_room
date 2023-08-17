# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import random
import uuid
from urllib.parse import urljoin

import django_filters
import requests
import six
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import InMemoryUploadedFile, SimpleUploadedFile
from django.core.validators import URLValidator
from django.forms import NullBooleanSelect
from django.utils.timezone import now as django_now
from django_filters.constants import EMPTY_VALUES
from django_filters.fields import Lookup
from django_filters.filterset import FILTER_FOR_DBFIELD_DEFAULTS
from django.db import models
from django import forms
from django_filters.widgets import QueryArrayWidget
from drf_extra_fields.fields import Base64ImageField
from imagekit.models import ProcessedImageField
from rest_framework import exceptions, fields, serializers
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response


class NullBooleanField(forms.NullBooleanField):
    widget = NullBooleanSelect


class BooleanFilter(django_filters.BooleanFilter):
    field_class = NullBooleanField


FILTER_FOR_DBFIELD_DEFAULTS[models.BooleanField] = {'filter_class': BooleanFilter}


class AllMixin(object):
    LIMIT = 2000

    @action(methods=['get'], detail=False)
    def all(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        if queryset.count() > self.LIMIT:
            raise exceptions.ValidationError('数据太多，不能一次性获取%s条数据，该情况请做分页处理' % self.LIMIT)

        serializer = self.get_serializer(queryset, many=True)
        return Response({'detail': serializer.data})


class FormRangeMixin(object):
    def to_python(self, value):
        """
        datalist 的验证
        """

        if value in self.empty_values:
            return None

        # 前端传入的无序时间，需要重新排序
        value.sort()

        date_list = []
        for d in value:
            df = super(FormRangeMixin, self).to_python(d)
            if not df:
                return None
            date_list.append(df)

        # 如果等于1. 说明值重复了
        if len(date_list) == 1:
            date_list.append(date_list[0])

        return sorted(date_list)


class FormsDateField(FormRangeMixin, forms.DateField):
    pass


class DateListFilter(django_filters.DateFilter):
    field_class = FormsDateField

    def __init__(self, widget=QueryArrayWidget, **kwargs):
        super(DateListFilter, self).__init__(widget=widget, **kwargs)


class IntegerFilter(django_filters.CharFilter):
    field_class = forms.IntegerField


class MonthFilter(IntegerFilter):
    """
    根据月份查询。
    """

    def filter(self, qs, value):
        if isinstance(value, Lookup):
            lookup = six.text_type(value.lookup_type)
            value = value.value
        else:
            lookup = self.lookup_expr
        if value in EMPTY_VALUES:
            return qs
        if self.distinct:
            qs = qs.distinct()

        month = abs(value)
        value = django_now() - relativedelta(months=month)

        qs = self.get_method(qs)(**{'%s__%s' % (self.field_name, lookup): value})
        return qs


# # 自定义验证码样式
# class CustomCaptcha(ImageCaptcha):
#     table = []
#     for i in range(256):
#         table.append(i * 1.97)
#
#     def create_captcha_image(self, chars, color, background):
#         """Create the CAPTCHA image itself.
#
#         :param chars: text to be generated.
#         :param color: color of the text.
#         :param background: color of the background.
#
#         The color should be a tuple of 3 numbers, such as (0, 255, 255).
#         """
#         image = Image.new('RGB', (self._width, self._height), background)
#         draw = Draw(image)
#
#         def _draw_character(c):
#             font = random.choice(self.truefonts)
#             w, h = draw.textsize(c, font=font)
#
#             dx = random.randint(0, 4)
#             dy = random.randint(0, 6)
#             im = Image.new('RGBA', (w + dx, h + dy))
#             Draw(im).text((dx, dy), c, font=font, fill=color)
#             return im
#
#         images = []
#         for c in chars:
#             images.append(_draw_character(c))
#
#         text_width = sum([im.size[0] for im in images])
#
#         width = max(text_width, self._width)
#         image = image.resize((width, self._height))
#
#         average = int(text_width / len(chars))
#         rand = int(0.25 * average)
#         offset = int(average * 0.1)
#
#         for im in images:
#             w, h = im.size
#             mask = im.convert('L').point(self.table)
#             image.paste(im, (offset, int((self._height - h) / 2)), mask)
#             offset = offset + w + random.randint(-rand, 0)
#
#         if width > self._width:
#             image = image.resize((self._width, self._height))
#
#         return image


# 封装一下请求class


class BaseRequest(object):
    def __init__(self, host):
        self.host = host

    def _url(self, url) -> str:
        return urljoin(self.host, url)

    def request(self, url, data, *, method="post", **kwargs):
        """
        通用request类 这里处理请求
        """

        data_map = {"method": method, "url": self._url(url), "timeout": 5}

        if method == "get":
            data_map.update({"params": data})
        else:
            data_map.update({"data": data})

        try:
            response = requests.request(**data_map, **kwargs)
        except (requests.ConnectionError, requests.Timeout) as e:
            raise exceptions.ValidationError('网络错误，无法连接系统！')
        except exceptions.ValidationError as e:
            raise exceptions.ValidationError(e)
        except Exception as e:
            logging.error(e)
            raise exceptions.ValidationError('未知错误，请联系管理员！')

        response = response.json()

        return response


class CustomMoneyField(fields.IntegerField):
    def to_internal_value(self, data):
        try:
            data = float(data)
        except ValueError:
            raise exceptions.ValidationError('金额要求是数字类型')

        return super(CustomMoneyField, self).to_internal_value(data * 10000)

    def to_representation(self, value):
        return "%.4f" % (value * 0.0001)


class CustomBase64ImageField(Base64ImageField):
    def __init__(self, *args, **kwargs):
        self.url_validator = URLValidator()
        super(CustomBase64ImageField, self).__init__(*args, **kwargs)

    @property
    def ALLOWED_TYPES(self):
        img_types = ('jpeg', 'jpg', 'png', 'gif', 'JPEG', 'JPG', 'PNG', 'GIF')
        return img_types

    def to_internal_value(self, base64_data):
        if isinstance(
                base64_data,
                InMemoryUploadedFile) and base64_data.name.split('.')[-1] in self.ALLOWED_TYPES:
            return super(fields.ImageField, self).to_internal_value(base64_data)

        if isinstance(base64_data, six.string_types) and base64_data.rsplit(
                '.', 1)[-1] in self.ALLOWED_TYPES:

            request = self.context.get('request')
            media_url = settings.MEDIA_URL
            if request is not None:
                host = '{scheme}://{host}'.format(scheme=request.scheme, host=request.get_host())
                if not media_url.startswith(host):
                    media_url = host + media_url

            if (self._verify_local_url(base64_data) and base64_data.startswith(media_url)):
                return base64_data.split(settings.MEDIA_URL)[-1]

            return self.to_local_img_path(base64_data).split(settings.MEDIA_URL)[-1]

        return super(CustomBase64ImageField, self).to_internal_value(base64_data)

    def to_local_img_path(self, url):
        """第三方图片路径转为本地图片路径"""

        url = self._valid_url(url)
        if not url:
            raise exceptions.ValidationError('图片路径不正确，请检查上传的图片路径是否正确')

        try:
            data = requests.get(url, timeout=3)
        except (requests.ConnectionError, requests.Timeout):
            raise exceptions.ValidationError('连接超时，无法获取第三方的图片数据，请检查上传的图片路径是否正确')
        except Exception as e:
            raise exceptions.ValidationError('未知错误，无法获取第三方的图片数据，请检查上传的图片路径是否正确')

        img = SimpleUploadedFile(
            '%s.%s' % (''.join(str(uuid.uuid1()).split('-')), url.rsplit('.')[-1]), data.content)

        return default_storage.url(default_storage.save(img.name, img))

    def _valid_url(self, url):
        try:
            self.url_validator(url)
        except ValidationError as e:
            return
        return url

    def _verify_local_url(self, url):
        """验证图片路径是否为本地路径"""

        if '*' in settings.ALLOWED_HOSTS:
            return True

        request = self.context.get('request')
        if request is None:
            return False

        scheme = '{scheme}://'.format(scheme=request.scheme)

        is_local_url = False

        for host in settings.ALLOWED_HOSTS:
            if url.startswith('%s%s' % (scheme, host)):
                is_local_url = True
        return is_local_url


class CustomListFilesField(serializers.ListField):
    def __init__(self, img_field_name='img', *args, **kwargs):
        self.img_field_name = img_field_name
        super(CustomListFilesField, self).__init__(*args, **kwargs)

    def to_representation(self, relate_field):
        if hasattr(relate_field, 'all'):
            return super(CustomListFilesField, self).to_representation(
                [getattr(i, self.img_field_name) for i in relate_field.all()])

        return super(CustomListFilesField, self).to_representation(relate_field)


class CustomModelSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        include_fields = kwargs.pop('fields', None)

        super(CustomModelSerializer, self).__init__(*args, **kwargs)

        self.serializer_field_mapping[ProcessedImageField] = CustomBase64ImageField

        if include_fields is not None:
            allowed = set(include_fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)
