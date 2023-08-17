from rest_framework import serializers


class UploadFileSerializer(serializers.Serializer):
    files = serializers.ListField(
        child=serializers.FileField(max_length=100000, allow_empty_file=False, use_url=False))

    class Meta:
        fields = ('files',)
