from django.urls import include, re_path
from rest_framework.routers import DefaultRouter
from common.rest import api

router = DefaultRouter()

urlpatterns = [
    re_path(r'^', include(router.urls)),
    re_path(r'^upload/$', api.UploadFileApiView.as_view(), name='upload_files'),
]

urlpatterns += router.urls
