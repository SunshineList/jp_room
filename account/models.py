from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
from imagekit.models import ProcessedImageField
from pilkit.processors import ResizeToFit


class User(AbstractUser):
    avatar = ProcessedImageField(upload_to="account/%Y/%m/",
                                 verbose_name='头像',
                                 null=True,
                                 blank=True,
                                 processors=[ResizeToFit(1000, 1000)],
                                 format='JPEG',
                                 options={'quality': settings.IMAGE_QUANLITY})

    class Meta:
        verbose_name = "账号"
        verbose_name_plural = verbose_name
        db_table = "account"
