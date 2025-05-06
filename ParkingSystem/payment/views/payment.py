from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
from django.urls import reverse
from django.contrib.sites.models import Site
import uuid
import datetime
import hashlib
import hmac
import json
import urllib.parse

from parking.models import Vehicle, ParkingTicket, ParkingTicketType, ParkingSession
from payment.models import Order, Payment
from helpers.vnpay import vnpay_create_payment_url, vnpay_verify_payment


class PaymentCreateView(LoginRequiredMixin, View):

    def get(self, request):
        ticket_type_id = request.GET.get('ticket_type')
        session_id = request.GET.get('session_id')
        ticket_id = request.GET.get('ticket_id')

        selected_vehicle = None
        ticket_type = None
        parking_session = None
        ticket = None
        payment_type = None

        vehicles = Vehicle.objects.filter(user=request.user, is_active=True)

        ticket_types = ParkingTicketType.objects.filter(is_active=True)

        if session_id:
            try:
                parking_session = ParkingSession.objects.get(id=session_id, user=request.user, status='active')
                selected_vehicle = parking_session.vehicle
                payment_type = 'session'
            except ParkingSession.DoesNotExist:
                messages.error(request, _("Không tìm thấy phiên đỗ xe!"))
                return redirect('parking:parking_history')

        if ticket_id:
            try:
                ticket = ParkingTicket.objects.get(id=ticket_id, user=request.user)
                selected_vehicle = ticket.vehicle
                payment_type = 'ticket'
            except ParkingTicket.DoesNotExist:
                messages.error(request, _("Không tìm thấy vé đỗ xe!"))
                return redirect('parking:parking_history')

        if ticket_type_id:
            try:
                ticket_type = ParkingTicketType.objects.get(id=ticket_type_id, is_active=True)
                payment_type = 'ticket'
            except ParkingTicketType.DoesNotExist:
                messages.error(request, _("Không tìm thấy loại vé!"))
                return redirect('home')

        context = {
            'vehicles': vehicles,
            'ticket_types': ticket_types,
            'selected_vehicle': selected_vehicle,
            'ticket_type': ticket_type,
            'parking_session': parking_session,
            'ticket': ticket,
            'payment_type': payment_type
        }

        return render(request, 'app/payment/payment_create.html', context)

    def post(self, request):
        payment_type = request.POST.get('payment_type')
        payment_method = request.POST.get('payment_method')
        vehicle_id = request.POST.get('vehicle_id')
        amount = 0
        order = None

        order_code = f"ORDER-{uuid.uuid4().hex[:8]}-{int(timezone.now().timestamp())}"

        if payment_type == 'ticket':
            ticket_type_id = request.POST.get('ticket_type_id')

            if not vehicle_id or not ticket_type_id:
                messages.error(request, _("Vui lòng chọn phương tiện và loại vé!"))
                return redirect('payment:create')

            try:
                vehicle = Vehicle.objects.get(id=vehicle_id, user=request.user, is_active=True)
                ticket_type = ParkingTicketType.objects.get(id=ticket_type_id, is_active=True)

                start_date = timezone.now()
                end_date = start_date + datetime.timedelta(hours=ticket_type.duration_hours)

                ticket = ParkingTicket.objects.create(
                    user=request.user,
                    vehicle=vehicle,
                    ticket_type=ticket_type,
                    start_date=start_date,
                    end_date=end_date,
                    status='active'
                )

                order = Order.objects.create(
                    user=request.user,
                    order_code=order_code,
                    parking_ticket=ticket,
                    order_type='ticket',
                    amount=ticket_type.price,
                    status='pending'
                )

                amount = ticket_type.price

            except (Vehicle.DoesNotExist, ParkingTicketType.DoesNotExist):
                messages.error(request, _("Dữ liệu không hợp lệ!"))
                return redirect('payment:create')

        elif payment_type == 'session':
            session_id = request.POST.get('session_id')

            if not session_id:
                messages.error(request, _("Không tìm thấy phiên đỗ xe!"))
                return redirect('payment:create')

            try:
                session = ParkingSession.objects.get(id=session_id, user=request.user)

                order = Order.objects.create(
                    user=request.user,
                    order_code=order_code,
                    parking_session=session,
                    order_type='session',
                    amount=session.total_cost,
                    status='pending'
                )

                amount = session.total_cost

            except ParkingSession.DoesNotExist:
                messages.error(request, _("Không tìm thấy phiên đỗ xe!"))
                return redirect('payment:create')
        else:
            messages.error(request, _("Loại thanh toán không hợp lệ!"))
            return redirect('payment:create')

        payment_code = f"PAY-{uuid.uuid4().hex[:8]}-{int(timezone.now().timestamp())}"

        payment = Payment.objects.create(
            order=order,
            payment_code=payment_code,
            payment_method=payment_method,
            amount=amount,
            status='pending'
        )

        if payment_method == 'vnpay':
            site = Site.objects.get(id=settings.SITE_ID)
            return_url = f"{request.scheme}://{site.domain}{reverse('payment:result')}"

            payment_url = vnpay_create_payment_url(
                request=request,
                order_id=order.order_code,
                amount=int(amount),
                order_desc=f"Thanh toan {payment_type}",
                return_url=return_url
            )

            request.session['payment_id'] = payment.id

            return redirect(payment_url)
        else:
            return redirect('payment:confirm')


class PaymentConfirmView(LoginRequiredMixin, View):
    """View xử lý xác nhận thanh toán"""

    def get(self, request):
        payment_id = request.session.get('payment_id')

        if not payment_id:
            messages.error(request, _("Không tìm thấy thông tin thanh toán!"))
            return redirect('payment:create')

        try:
            payment = Payment.objects.get(id=payment_id)
            order = payment.order

            context = {
                'payment': payment,
                'order': order
            }

            return render(request, 'app/payment/payment_confirm.html', context)

        except Payment.DoesNotExist:
            messages.error(request, _("Không tìm thấy thông tin thanh toán!"))
            return redirect('payment:create')

    def post(self, request):
        payment_id = request.session.get('payment_id')

        if not payment_id:
            messages.error(request, _("Không tìm thấy thông tin thanh toán!"))
            return redirect('payment:create')

        try:
            payment = Payment.objects.get(id=payment_id)
            order = payment.order

            payment.status = 'completed'
            payment.save()

            order.status = 'completed'
            order.save()

            if order.order_type == 'session':
                session = order.parking_session
                session.status = 'completed'
                session.save()

            if 'payment_id' in request.session:
                del request.session['payment_id']

            messages.success(request, _("Thanh toán thành công!"))
            return redirect('payment:result')

        except Payment.DoesNotExist:
            messages.error(request, _("Không tìm thấy thông tin thanh toán!"))
            return redirect('payment:create')


class PaymentResultView(LoginRequiredMixin, View):
    """View xử lý kết quả thanh toán"""

    def get(self, request):
        vnp_params = request.GET

        if vnp_params:
            is_valid = vnpay_verify_payment(vnp_params)

            if is_valid:
                order_code = vnp_params.get('vnp_TxnRef')

                try:
                    order = Order.objects.get(order_code=order_code)
                    payment = order.payment

                    payment.status = 'completed'
                    payment.payment_reference = vnp_params.get('vnp_TransactionNo')
                    payment.save()

                    order.status = 'completed'
                    order.save()

                    if order.order_type == 'session':
                        session = order.parking_session
                        session.status = 'completed'
                        session.save()

                    messages.success(request, _("Thanh toán thành công!"))

                except Order.DoesNotExist:
                    messages.error(request, _("Không tìm thấy thông tin đơn hàng!"))
            else:
                messages.error(request, _("Xác thực thanh toán thất bại!"))

        try:
            recent_payment = Payment.objects.filter(
                order__user=request.user,
                status='completed'
            ).latest('created_at')

            context = {
                'payment': recent_payment,
                'order': recent_payment.order
            }

            return render(request, 'app/payment/payment_result.html', context)

        except Payment.DoesNotExist:
            messages.info(request, _("Không tìm thấy thông tin thanh toán gần đây!"))
            return redirect('home')