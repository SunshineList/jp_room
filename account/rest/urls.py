# -*- coding: utf-8 -*-
from django.urls import path
from rest_framework.routers import DefaultRouter
from account.rest import api

router = DefaultRouter()

router.register("user", api.UserViewSet)

urlpatterns = [
    path('auth/', api.LoginApiView.as_view()),

]

urlpatterns += router.urls
