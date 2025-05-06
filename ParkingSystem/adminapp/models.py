from django.db import models
from django.utils.translation import gettext_lazy as _


class Configuration(models.Model):
    CONFIG_TYPE = (
        ('system', _('Hệ thống')),
        ('payment', _('Thanh toán')),
        ('parking', _('Bãi đỗ xe')),
        ('notification', _('Thông báo')),
        ('mail', _('Email')),
        ('ticket', _('Vé đỗ xe')),
    )

    key = models.CharField(_('Khóa'), max_length=100, unique=True)
    value = models.TextField(_('Giá trị'))
    config_type = models.CharField(_('Loại cấu hình'), max_length=20, choices=CONFIG_TYPE, default='system')
    description = models.TextField(_('Mô tả'), blank=True, null=True)
    is_active = models.BooleanField(_('Đang hoạt động'), default=True)
    created_at = models.DateTimeField(_('Ngày tạo'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Ngày cập nhật'), auto_now=True)

    class Meta:
        verbose_name = _('Cấu hình')
        verbose_name_plural = _('Cấu hình')

    def __str__(self):
        return f"{self.key} - {self.config_type}"


class Notification(models.Model):
    NOTIFICATION_TYPE = (
        ('system', _('Hệ thống')),
        ('payment', _('Thanh toán')),
        ('parking', _('Bãi đỗ xe')),
        ('promotional', _('Khuyến mãi')),
    )

    user = models.ForeignKey('account.User', on_delete=models.CASCADE, related_name='notifications',
                             verbose_name=_('Người dùng'))
    title = models.CharField(_('Tiêu đề'), max_length=255)
    message = models.TextField(_('Nội dung'))
    notification_type = models.CharField(_('Loại thông báo'), max_length=20, choices=NOTIFICATION_TYPE)
    is_read = models.BooleanField(_('Đã đọc'), default=False)
    created_at = models.DateTimeField(_('Ngày tạo'), auto_now_add=True)

    class Meta:
        verbose_name = _('Thông báo')
        verbose_name_plural = _('Thông báo')

    def __str__(self):
        return f"{self.user.username} - {self.title}"