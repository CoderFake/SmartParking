from django.shortcuts import render, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from parking.models import ParkingSession, Vehicle
from django.utils import timezone
from django.db.models import Q


class ParkingHistoryView(LoginRequiredMixin, View):
    def get(self, request):
        sessions = ParkingSession.objects.filter(
            user=request.user
        ).order_by('-entry_time')

        status_filter = request.GET.get('status')
        vehicle_filter = request.GET.get('vehicle')
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')

        filters = Q()

        if status_filter and status_filter != 'all':
            filters &= Q(status=status_filter)

        if vehicle_filter and vehicle_filter != 'all':
            filters &= Q(vehicle_id=vehicle_filter)

        if date_from:
            filters &= Q(entry_time__gte=date_from)

        if date_to:
            filters &= Q(entry_time__lte=date_to)

        sessions = sessions.filter(filters)
        vehicles = Vehicle.objects.filter(user=request.user, is_active=True)

        context = {
            'sessions': sessions,
            'vehicles': vehicles,
            'status_filter': status_filter,
            'vehicle_filter': vehicle_filter,
            'date_from': date_from,
            'date_to': date_to
        }

        return render(request, 'app/parking/parking_history.html', context)


class ParkingDetailView(LoginRequiredMixin, View):
    def get(self, request, pk):
        session = get_object_or_404(ParkingSession, pk=pk, user=request.user)

        # Tính thời gian đỗ xe hiện tại nếu chưa kết thúc
        if session.status == 'active' and not session.exit_time:
            current_duration = timezone.now() - session.entry_time
            session.current_duration = current_duration

        context = {
            'session': session
        }

        return render(request, 'app/parking/parking_detail.html', context)