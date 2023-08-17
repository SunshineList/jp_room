# -*- coding: utf-8 -*-
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from account.models import User
from common.utils import CustomModelSerializer


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, error_messages={'blank': '用户名不能为空'})
    password = serializers.CharField(style={'input_type': 'password'},
                                     required=True,
                                     error_messages={'blank': '密码不能为空'})

    def validate(self, attrs):
        username, password = attrs['username'], attrs['password']

        user = authenticate(username=username, password=password)

        if not user:
            raise ValidationError('用户名或者密码错误!')

        attrs['user'] = user
        return attrs


class PasswordSerializer(serializers.Serializer):
    password = serializers.CharField(style={'input_type': 'password'},
                                     required=True,
                                     error_messages={'blank': '当前密码不能为空'})
    new_password = serializers.CharField(style={'input_type': 'password'},
                                         required=True,
                                         error_messages={'blank': '新密码不能为空'})

    repeat_password = serializers.CharField(style={'input_type': 'password'},
                                            required=True,
                                            error_messages={'blank': '请重复输入新密码'})

    def validate(self, attrs):

        user = self.context["request"].user

        password, new_password, repeat_password = attrs["password"], attrs["new_password"], attrs[
            "repeat_password"]

        if not check_password(password, user.password):
            raise ValidationError("当前密码输入错误")

        if new_password != repeat_password:
            raise ValidationError("两次密码输入不一致")

        user.set_password(new_password)
        user.save()

        return attrs


class RegisterSerializers(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("username", "password")

    def create(self, validated_data):
        password = validated_data.pop("password")
        instance = super(RegisterSerializers, self).create(validated_data)
        instance.set_password(password)
        instance.save()
        return instance


class UserInfoSerializers(CustomModelSerializer):
    class Meta:
        model = User
        fields = "__all__"
