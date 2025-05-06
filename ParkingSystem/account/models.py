from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    USER_STATUS = (
        ('active', _('Hoạt động')),
        ('inactive', _('Không hoạt động')),
        ('pending', _('Đang chờ')),
        ('blocked', _('Đã khóa')),
    )

    USER_TYPE = (
        ('admin', _('Quản trị viên')),
        ('staff', _('Nhân viên')),
        ('customer', _('Khách hàng')),
    )

    email = models.EmailField(_('Địa chỉ email'), unique=True)
    phone_number = models.CharField(_('Số điện thoại'), max_length=20, blank=True, null=True)
    status = models.CharField(_('Trạng thái'), max_length=10, choices=USER_STATUS, default='pending')
    user_type = models.CharField(_('Loại người dùng'), max_length=10, choices=USER_TYPE, default='customer')
    created_at = models.DateTimeField(_('Ngày tạo'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Ngày cập nhật'), auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = _('Người dùng')
        verbose_name_plural = _('Người dùng')

    def __str__(self):
        return self.username


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name=_('Người dùng'))
    full_name = models.CharField(_('Họ và tên'), max_length=255, blank=True, null=True)
    address = models.CharField(_('Địa chỉ'), max_length=255, blank=True, null=True)
    avatar = models.ImageField(_('Ảnh đại diện'), upload_to='avatars/', blank=True, null=True)
    date_of_birth = models.DateField(_('Ngày sinh'), blank=True, null=True)
    created_at = models.DateTimeField(_('Ngày tạo'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Ngày cập nhật'), auto_now=True)

    class Meta:
        verbose_name = _('Hồ sơ')
        verbose_name_plural = _('Hồ sơ')

    def __str__(self):
        return f"Hồ sơ của {self.user.username}"

