from django.db import models
from rest_framework import exceptions

# Create your models here.
from jp.utils import list_to_choice


def validate_password(value):
    if len(value) < 4:
        raise exceptions.ValidationError("最少要4位口令")
    return value


class JpRoom(models.Model):
    STATUS = list_to_choice(["未开始", "进行中", "已结束"])

    room_id = models.CharField("房间号", max_length=20, unique=True)
    password = models.PositiveIntegerField("口令", max_length=8, validators=[validate_password, ])
    status = models.CharField("房间状态", max_length=20, default="未开始", choices=STATUS)
    total_people = models.PositiveIntegerField("总人数", default=3)
    result_time = models.PositiveIntegerField("出结果时间(ms)", default=3000)

    created_time = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "房间信息"
        verbose_name_plural = verbose_name
