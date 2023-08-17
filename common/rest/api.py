import uuid

from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.validators import URLValidator
from rest_framework import permissions
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from rest_framework.response import Response

from common.rest.serializers import UploadFileSerializer


class UploadFileApiView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = (permissions.IsAuthenticated,)
    tags = ["文件上传", ]

    def post(self, request):
        serializer = UploadFileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        files = serializer.validated_data['files']
        print(files)
        file_urls = []
        for f in files:
            uuid_name = ''.join(str(uuid.uuid1()).split('-')) + '.' + f.name.split('.')[-1]
            file_name = default_storage.save(uuid_name, f)

            host = '{scheme}://{host}'.format(scheme=request.scheme, host=request.get_host())
            file_url = default_storage.url(file_name)
            url_validator = URLValidator()

            try:
                url_validator(file_url)
            except ValidationError as e:
                file_url = '{host}{file_url}'.format(host=host, file_url=file_url)

            file_urls.append(file_url)

        return Response({'results': file_urls})
