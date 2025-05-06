from django.db import models
from django.utils.translation import gettext_lazy as _
from account.models import User


class ParkingLot(models.Model):
    name = models.CharField(_('Tên bãi đỗ xe'), max_length=255)
    address = models.CharField(_('Địa chỉ'), max_length=255)
    description = models.TextField(_('Mô tả'), blank=True, null=True)
    total_slots = models.IntegerField(_('Tổng số vị trí'), default=0)
    available_slots = models.IntegerField(_('Số vị trí còn trống'), default=0)
    total_floors = models.IntegerField(_('Tổng số tầng'), default=1)
    entry_camera_url = models.URLField(_('URL camera vào'), blank=True, null=True)
    exit_camera_url = models.URLField(_('URL camera ra'), blank=True, null=True)
    mqtt_topic = models.CharField(_('Chủ đề MQTT'), max_length=100, blank=True, null=True)
    bucket_name = models.CharField(_('Tên bucket Minio'), max_length=100, blank=True, null=True)
    is_active = models.BooleanField(_('Đang hoạt động'), default=True)
    created_at = models.DateTimeField(_('Ngày tạo'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Ngày cập nhật'), auto_now=True)

    class Meta:
        verbose_name = _('Bãi đỗ xe')
        verbose_name_plural = _('Bãi đỗ xe')

    def __str__(self):
        return self.name


class ParkingFloor(models.Model):
    parking_lot = models.ForeignKey(ParkingLot, on_delete=models.CASCADE, related_name='floors',
                                    verbose_name=_('Bãi đỗ xe'))
    floor_number = models.IntegerField(_('Số tầng'))
    name = models.CharField(_('Tên tầng'), max_length=100)
    total_slots = models.IntegerField(_('Tổng số vị trí'), default=0)
    available_slots = models.IntegerField(_('Số vị trí còn trống'), default=0)
    total_car_slots = models.IntegerField(_('Tổng số vị trí ô tô'), default=0)
    available_car_slots = models.IntegerField(_('Số vị trí ô tô còn trống'), default=0)
    total_motorbike_slots = models.IntegerField(_('Tổng số vị trí xe máy'), default=0)
    available_motorbike_slots = models.IntegerField(_('Số vị trí xe máy còn trống'), default=0)
    is_active = models.BooleanField(_('Đang hoạt động'), default=True)
    created_at = models.DateTimeField(_('Ngày tạo'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Ngày cập nhật'), auto_now=True)

    class Meta:
        verbose_name = _('Tầng đỗ xe')
        verbose_name_plural = _('Tầng đỗ xe')
        unique_together = ('parking_lot', 'floor_number')
        ordering = ['floor_number']

    def __str__(self):
        return f"{self.parking_lot.name} - Tầng {self.floor_number} ({self.name})"


class ParkingSlot(models.Model):
    SLOT_STATUS = (
        ('available', _('Trống')),
        ('occupied', _('Đã đỗ')),
        ('reserved', _('Đã đặt trước')),
        ('maintenance', _('Bảo trì')),
    )

    SLOT_TYPE = (
        ('car', _('Ô tô')),
        ('motorbike', _('Xe máy')),
    )

    parking_lot = models.ForeignKey(ParkingLot, on_delete=models.CASCADE, related_name='slots',
                                    verbose_name=_('Bãi đỗ xe'))
    parking_floor = models.ForeignKey(ParkingFloor, on_delete=models.CASCADE, related_name='slots',
                                      verbose_name=_('Tầng đỗ xe'))
    slot_number = models.CharField(_('Số vị trí'), max_length=10)
    slot_type = models.CharField(_('Loại vị trí'), max_length=20, choices=SLOT_TYPE, default='car')
    status = models.CharField(_('Trạng thái'), max_length=20, choices=SLOT_STATUS, default='available')
    sensor_id = models.CharField(_('Mã cảm biến'), max_length=50, null=True, blank=True)
    is_active = models.BooleanField(_('Đang hoạt động'), default=True)
    created_at = models.DateTimeField(_('Ngày tạo'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Ngày cập nhật'), auto_now=True)

    class Meta:
        verbose_name = _('Vị trí đỗ xe')
        verbose_name_plural = _('Vị trí đỗ xe')
        unique_together = ('parking_floor', 'slot_number')

    def __str__(self):
        return f"{self.parking_lot.name} - Tầng {self.parking_floor.floor_number} - {self.slot_number} ({self.get_slot_type_display()})"


class Vehicle(models.Model):
    VEHICLE_TYPE = (
        ('car', _('Ô tô')),
        ('motorbike', _('Xe máy')),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehicles', verbose_name=_('Người dùng'))
    license_plate = models.CharField(_('Biển số xe'), max_length=20)
    vehicle_type = models.CharField(_('Loại phương tiện'), max_length=20, choices=VEHICLE_TYPE)
    make = models.CharField(_('Hãng xe'), max_length=50, blank=True, null=True)
    model = models.CharField(_('Mẫu xe'), max_length=50, blank=True, null=True)
    color = models.CharField(_('Màu sắc'), max_length=30, blank=True, null=True)
    rfid_tag = models.CharField(_('Thẻ RFID'), max_length=100, blank=True, null=True)
    is_active = models.BooleanField(_('Đang hoạt động'), default=True)
    created_at = models.DateTimeField(_('Ngày tạo'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Ngày cập nhật'), auto_now=True)

    class Meta:
        verbose_name = _('Phương tiện')
        verbose_name_plural = _('Phương tiện')
        unique_together = ('user', 'license_plate')

    def __str__(self):
        return f"{self.license_plate} - {self.get_vehicle_type_display()}"


class ParkingTicketType(models.Model):
    TICKET_TYPE = (
        ('daily', _('Ngày')),
        ('monthly', _('Tháng')),
        ('day_night', _('Ngày/Đêm')),
    )

    VEHICLE_TYPE = (
        ('car', _('Ô tô')),
        ('motorbike', _('Xe máy')),
    )

    name = models.CharField(_('Tên loại vé'), max_length=100)
    description = models.TextField(_('Mô tả'), blank=True, null=True)
    ticket_type = models.CharField(_('Loại vé'), max_length=20, choices=TICKET_TYPE)
    vehicle_type = models.CharField(_('Loại phương tiện'), max_length=20, choices=VEHICLE_TYPE)
    price = models.DecimalField(_('Giá vé'), max_digits=10, decimal_places=0)
    duration_hours = models.IntegerField(_('Thời hạn (giờ)'), default=24)
    is_active = models.BooleanField(_('Đang hoạt động'), default=True)
    created_at = models.DateTimeField(_('Ngày tạo'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Ngày cập nhật'), auto_now=True)

    class Meta:
        verbose_name = _('Loại vé đỗ xe')
        verbose_name_plural = _('Loại vé đỗ xe')

    def __str__(self):
        return f"{self.name} - {self.get_ticket_type_display()} - {self.get_vehicle_type_display()}"


class ParkingTicket(models.Model):
    TICKET_STATUS = (
        ('active', _('Đang sử dụng')),
        ('expired', _('Hết hạn')),
        ('cancelled', _('Đã hủy')),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='parking_tickets',
                             verbose_name=_('Người dùng'))
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='tickets',
                                verbose_name=_('Phương tiện'))
    ticket_type = models.ForeignKey(ParkingTicketType, on_delete=models.CASCADE, related_name='tickets',
                                    verbose_name=_('Loại vé'))
    start_date = models.DateTimeField(_('Ngày bắt đầu'))
    end_date = models.DateTimeField(_('Ngày kết thúc'))
    status = models.CharField(_('Trạng thái'), max_length=20, choices=TICKET_STATUS, default='active')
    created_at = models.DateTimeField(_('Ngày tạo'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Ngày cập nhật'), auto_now=True)

    class Meta:
        verbose_name = _('Vé đỗ xe')
        verbose_name_plural = _('Vé đỗ xe')

    def __str__(self):
        return f"{self.vehicle.license_plate} - {self.ticket_type.name} - {self.start_date.date()} đến {self.end_date.date()}"


class ParkingSession(models.Model):
    SESSION_STATUS = (
        ('active', _('Đang đỗ')),
        ('completed', _('Đã hoàn thành')),
        ('cancelled', _('Đã hủy')),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='parking_sessions',
                             verbose_name=_('Người dùng'))
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='parking_sessions',
                                verbose_name=_('Phương tiện'))
    parking_lot = models.ForeignKey(ParkingLot, on_delete=models.CASCADE, related_name='parking_sessions',
                                    verbose_name=_('Bãi đỗ xe'))
    parking_slot = models.ForeignKey(ParkingSlot, on_delete=models.CASCADE, related_name='parking_sessions', null=True,
                                     blank=True, verbose_name=_('Vị trí đỗ xe'))
    ticket = models.ForeignKey(ParkingTicket, on_delete=models.SET_NULL, related_name='parking_sessions', null=True,
                               blank=True, verbose_name=_('Vé đỗ xe'))
    entry_time = models.DateTimeField(_('Thời gian vào'))
    exit_time = models.DateTimeField(_('Thời gian ra'), blank=True, null=True)
    duration = models.DurationField(_('Thời gian đỗ'), blank=True, null=True)
    entry_image = models.CharField(_('Ảnh vào'), max_length=255, blank=True, null=True)
    exit_image = models.CharField(_('Ảnh ra'), max_length=255, blank=True, null=True)
    status = models.CharField(_('Trạng thái'), max_length=20, choices=SESSION_STATUS, default='active')
    total_cost = models.DecimalField(_('Tổng chi phí'), max_digits=10, decimal_places=0, default=0)
    created_at = models.DateTimeField(_('Ngày tạo'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Ngày cập nhật'), auto_now=True)

    class Meta:
        verbose_name = _('Phiên đỗ xe')
        verbose_name_plural = _('Phiên đỗ xe')

    def __str__(self):
        return f"{self.vehicle.license_plate} - {self.entry_time}"