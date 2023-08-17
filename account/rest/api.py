# -*- coding: utf-8 -*-
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, permissions
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from account.models import User
from account.rest.serializers import LoginSerializer, UserInfoSerializers, PasswordSerializer, RegisterSerializers


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return


class LoginApiView(APIView):
    permission_classes = (AllowAny,)
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    serializer_class = LoginSerializer

    schema = openapi.Schema(type=openapi.TYPE_OBJECT,
                            required=['username', 'password'],
                            properties={
                                'username': openapi.Schema('用户名', type=openapi.TYPE_STRING),
                                'password': openapi.Schema('密码', type=openapi.TYPE_STRING)
                            })

    @swagger_auto_schema(request_body=schema, tags=["登录"])
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)

        return Response({'token': token.key})

    @swagger_auto_schema(tags=["退出登录"])
    def delete(self, request, *args, **kwargs):
        """
        退出登录， 删除Token
        """
        if request.user.is_authenticated:
            Token.objects.filter(user=self.request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserInfoSerializers
    permission_classes = (permissions.IsAuthenticated,)
    tags = ["账号管理", ]

    @action(methods=["get"], detail=False)
    def change_password(self, request, *args, **kwargs):
        ser_data = PasswordSerializer(data=request.data, context={"request": request})
        ser_data.is_valid(raise_exception=True)
        return Response({"message": "密码修改成功"})

    @action(methods=["get"], detail=False)
    def mine(self, request, *args, **kwargs):
        data = UserInfoSerializers(request.user, context={'request': request}).data
        return Response(data)

    @action(methods=["post"], detail=False)
    @swagger_auto_schema(request_body=RegisterSerializers)
    def register(self, request, *args, **kwargs):
        ser_data = RegisterSerializers(data=self.request.data)
        ser_data.is_valid(raise_exception=True)
        ser_data.save()
        return Response("注册成功")
