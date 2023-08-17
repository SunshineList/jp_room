# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""
这是django rest错误处理
"""
from __future__ import unicode_literals

import copy

# from rest_framework.views import exception_handler
import traceback

from django.db import IntegrityError
from django.http import Http404
from rest_framework import exceptions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import set_rollback


def _generate_errors_from_list(data, **kwargs):
    """Create error objects based on the exception."""
    errors = []
    status_code = kwargs.get("code", 0)
    source = kwargs.get("source")
    for value in data:
        if isinstance(value, str):
            new_error = {"detail": value, "source": source, "status": status_code}
            errors.append(new_error)
        elif isinstance(value, list):
            errors += _generate_errors_from_list(value, **kwargs)
        elif isinstance(value, dict):
            errors += _generate_errors_from_dict(value, **kwargs)
    return errors


def _generate_errors_from_dict(data, **kwargs):
    """Create error objects based on the exception."""
    errors = []
    status_code = kwargs.get("code", 0)
    source = kwargs.get("source")
    for key, value in data.items():
        source_val = f"{source}.{key}" if source else key
        if isinstance(value, str):
            new_error = {"detail": value, "source": source_val, "status": status_code}
            errors.append(new_error)
        elif isinstance(value, list):
            kwargs["source"] = source_val
            errors += _generate_errors_from_list(value, **kwargs)
        elif isinstance(value, dict):
            kwargs["source"] = source_val
            errors += _generate_errors_from_dict(value, **kwargs)
    return errors


def exception_handler(exc, context):
    """
    Returns the response that should be used for any given exception.

    By default we handle the REST framework `APIException`, and also
    Django's built-in `Http404` and `PermissionDenied` exceptions.

    Any unhandled exceptions may return `None`, which will cause a 500 error
    to be raised.
    """
    if isinstance(exc, Http404):
        exc = exceptions.NotFound()
    elif isinstance(exc, PermissionDenied):
        exc = exceptions.PermissionDenied()

    elif isinstance(exc, IntegrityError):
        detail = str(exc).split("DETAIL:")[1].replace("\"", "").replace("\n", "")
        exc = exceptions.APIException(detail=detail, code=400)

    if isinstance(exc, exceptions.APIException):
        headers = {}
        if getattr(exc, 'auth_header', None):
            headers['WWW-Authenticate'] = exc.auth_header
        if getattr(exc, 'wait', None):
            headers['Retry-After'] = '%d' % exc.wait

        if isinstance(exc.detail, (list, dict)):
            data = exc.detail
        else:
            data = {'detail': exc.detail}

        set_rollback()
        return Response(data, status=exc.status_code, headers=headers)

    return None


def my_exception_handler(exc, context):
    response = exception_handler(exc, context)
    print("exc", exc, response, type(exc))
    e_str = ""

    status_code = 400

    if isinstance(exc, AssertionError):
        return Response(status=status_code, data={'msg': str(exc).split("detail:")[0], 'code': status_code})
    try:
        status_code = exc.status_code
    except:
        pass
    # Now add the HTTP status code to the response.
    if response is not None:
        errors = []
        data = copy.deepcopy(response.data)
        if isinstance(data, dict):
            errors += _generate_errors_from_dict(data)
        elif isinstance(data, list):
            errors += _generate_errors_from_list(data)
        for key, error in enumerate(errors):
            source = error.get('source') and error.get('source')
            if source == "non_field_errors":
                source = ""
            else:
                source = source and source + ":" or ""
            e_str += "%s%s" % (source, error.get('detail'))
            if key != (len(errors) - 1):
                e_str += ";"
        error_response = {"msg": e_str, "code": status_code}
        response.data = error_response
    else:
        # data = {'detail': exc.detail}
        data = {"msg": '', "code": 400}  #
        msg = []
        response = Response(data, status=400)
        # print("type", type(exc.messages), exc.messages)
        # print("execcc",,exc)
        # if isinstance(exc.messages, list):
        #     msg = ";".join(exc.messages)
        # if isinstance(exc.messages, dict):
        #     for key, item in exc.messages:
        #         print("item", item)
        #         msg += item
        #     msg = ";".join(msg)
        traceback.print_exc()

        data["msg"] = exc.__repr__()
        response.data = data
    return response
