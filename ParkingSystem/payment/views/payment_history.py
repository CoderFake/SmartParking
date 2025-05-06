from django.shortcuts import render, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from payment.models import Order, Payment
from django.db.models import Q


class PaymentHistoryView(LoginRequiredMixin, View):
    """View hiển thị lịch sử thanh toán"""

    def get(self, request):
        status_filter = request.GET.get('status')
        payment_method_filter = request.GET.get('payment_method')
        order_type_filter = request.GET.get('order_type')
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')

        payments = Payment.objects.filter(order__user=request.user).order_by('-created_at')

        filters = Q()

        if status_filter and status_filter != 'all':
            filters &= Q(status=status_filter)

        if payment_method_filter and payment_method_filter != 'all':
            filters &= Q(payment_method=payment_method_filter)

        if order_type_filter and order_type_filter != 'all':
            filters &= Q(order__order_type=order_type_filter)

        if date_from:
            filters &= Q(created_at__gte=date_from)

        if date_to:
            filters &= Q(created_at__lte=date_to)

        payments = payments.filter(filters)

        context = {
            'payments': payments,
            'status_filter': status_filter,
            'payment_method_filter': payment_method_filter,
            'order_type_filter': order_type_filter,
            'date_from': date_from,
            'date_to': date_to
        }

        return render(request, 'app/payment/payment_history.html', context)


class PaymentDetailView(LoginRequiredMixin, View):
    """View hiển thị chi tiết thanh toán"""

    def get(self, request, pk):
        payment = get_object_or_404(Payment, pk=pk, order__user=request.user)
        order = payment.order

        context = {
            'payment': payment,
            'order': order
        }

        return render(request, 'app/payment/payment_detail.html', context)