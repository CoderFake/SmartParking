from django.urls import path
from payment.views.payment import PaymentCreateView, PaymentConfirmView, PaymentResultView
from payment.views.payment_history import PaymentHistoryView, PaymentDetailView

app_name = 'payment'

urlpatterns = [
    # Thanh toán
    path('create/', PaymentCreateView.as_view(), name='create'),
    path('confirm/', PaymentConfirmView.as_view(), name='confirm'),
    path('result/', PaymentResultView.as_view(), name='result'),

    # Lịch sử thanh toán
    path('history/', PaymentHistoryView.as_view(), name='history'),
    path('history/<int:pk>/', PaymentDetailView.as_view(), name='detail'),
]