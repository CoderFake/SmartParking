from django.db import models
from django.utils.translation import gettext_lazy as _
from account.models import User
from parking.models import ParkingSession, ParkingTicket


class Order(models.Model):
    ORDER_STATUS = (
        ('pending', _('Đang chờ')),
        ('completed', _('Đã hoàn thành')),
        ('cancelled', _('Đã hủy')),
    )

    ORDER_TYPE = (
        ('ticket', _('Mua vé')),
        ('session', _('Thanh toán phiên đỗ xe')),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', verbose_name=_('Người dùng'))
    order_code = models.CharField(_('Mã đơn hàng'), max_length=50, unique=True)
    parking_ticket = models.ForeignKey(ParkingTicket, on_delete=models.SET_NULL, related_name='orders', null=True,
                                       blank=True, verbose_name=_('Vé đỗ xe'))
    parking_session = models.ForeignKey(ParkingSession, on_delete=models.SET_NULL, related_name='orders', null=True,
                                        blank=True, verbose_name=_('Phiên đỗ xe'))
    order_type = models.CharField(_('Loại đơn hàng'), max_length=20, choices=ORDER_TYPE)
    amount = models.DecimalField(_('Số tiền'), max_digits=10, decimal_places=0)
    status = models.CharField(_('Trạng thái'), max_length=20, choices=ORDER_STATUS, default='pending')
    notes = models.TextField(_('Ghi chú'), blank=True, null=True)
    created_at = models.DateTimeField(_('Ngày tạo'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Ngày cập nhật'), auto_now=True)

    class Meta:
        verbose_name = _('Đơn hàng')
        verbose_name_plural = _('Đơn hàng')

    def __str__(self):
        return f"{self.order_code} - {self.amount} VNĐ"


class Payment(models.Model):
    PAYMENT_STATUS = (
        ('pending', _('Đang chờ')),
        ('completed', _('Đã hoàn thành')),
        ('failed', _('Thất bại')),
        ('refunded', _('Đã hoàn tiền')),
    )

    PAYMENT_METHOD = (
        ('vnpay', _('VNPay')),
        ('cash', _('Tiền mặt')),
        ('bank_transfer', _('Chuyển khoản')),
        ('wallet', _('Ví điện tử')),
    )

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment', verbose_name=_('Đơn hàng'))
    payment_code = models.CharField(_('Mã thanh toán'), max_length=50, unique=True)
    payment_method = models.CharField(_('Phương thức thanh toán'), max_length=20, choices=PAYMENT_METHOD)
    amount = models.DecimalField(_('Số tiền'), max_digits=10, decimal_places=0)
    payment_date = models.DateTimeField(_('Ngày thanh toán'), auto_now_add=True)
    payment_reference = models.CharField(_('Mã tham chiếu thanh toán'), max_length=100, blank=True, null=True)
    status = models.CharField(_('Trạng thái'), max_length=20, choices=PAYMENT_STATUS, default='pending')
    notes = models.TextField(_('Ghi chú'), blank=True, null=True)
    created_at = models.DateTimeField(_('Ngày tạo'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Ngày cập nhật'), auto_now=True)

    class Meta:
        verbose_name = _('Thanh toán')
        verbose_name_plural = _('Thanh toán')

    def __str__(self):
        return f"{self.payment_code} - {self.amount} VNĐ"
