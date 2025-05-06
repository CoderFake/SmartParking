from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import gettext_lazy as _
from parking.models import Vehicle


class VehicleListView(LoginRequiredMixin, View):
    def get(self, request):
        vehicles = Vehicle.objects.filter(user=request.user, is_active=True)
        context = {
            'vehicles': vehicles
        }
        return render(request, 'app/parking/vehicle_list.html', context)


class VehicleCreateView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'app/parking/vehicle_form.html')

    def post(self, request):
        license_plate = request.POST.get('license_plate')
        vehicle_type = request.POST.get('vehicle_type')
        make = request.POST.get('make')
        model = request.POST.get('model')
        color = request.POST.get('color')
        rfid_tag = request.POST.get('rfid_tag')

        if not license_plate or not vehicle_type:
            messages.error(request, _("Vui lòng điền đầy đủ thông tin bắt buộc"))
            return render(request, 'app/parking/vehicle_form.html')

        if Vehicle.objects.filter(user=request.user, license_plate=license_plate, is_active=True).exists():
            messages.error(request, _("Biển số xe này đã được đăng ký"))
            return render(request, 'app/parking/vehicle_form.html')

        vehicle = Vehicle.objects.create(
            user=request.user,
            license_plate=license_plate,
            vehicle_type=vehicle_type,
            make=make,
            model=model,
            color=color,
            rfid_tag=rfid_tag
        )

        messages.success(request, _("Thêm phương tiện thành công!"))
        return redirect('parking:vehicle_list')


class VehicleUpdateView(LoginRequiredMixin, View):
    def get(self, request, pk):
        vehicle = get_object_or_404(Vehicle, pk=pk, user=request.user, is_active=True)
        context = {
            'vehicle': vehicle
        }
        return render(request, 'app/parking/vehicle_form.html', context)

    def post(self, request, pk):
        vehicle = get_object_or_404(Vehicle, pk=pk, user=request.user, is_active=True)

        license_plate = request.POST.get('license_plate')
        vehicle_type = request.POST.get('vehicle_type')
        make = request.POST.get('make')
        model = request.POST.get('model')
        color = request.POST.get('color')
        rfid_tag = request.POST.get('rfid_tag')

        if not license_plate or not vehicle_type:
            messages.error(request, _("Vui lòng điền đầy đủ thông tin bắt buộc"))
            context = {
                'vehicle': vehicle
            }
            return render(request, 'app/parking/vehicle_form.html', context)

        if Vehicle.objects.filter(user=request.user, license_plate=license_plate, is_active=True).exclude(pk=pk).exists():
            messages.error(request, _("Biển số xe này đã được đăng ký"))
            context = {
                'vehicle': vehicle
            }
            return render(request, 'app/parking/vehicle_form.html', context)

        vehicle.license_plate = license_plate
        vehicle.vehicle_type = vehicle_type
        vehicle.make = make
        vehicle.model = model
        vehicle.color = color
        vehicle.rfid_tag = rfid_tag
        vehicle.save()

        messages.success(request, _("Cập nhật phương tiện thành công!"))
        return redirect('parking:vehicle_list')


class VehicleDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        vehicle = get_object_or_404(Vehicle, pk=pk, user=request.user, is_active=True)
        vehicle.is_active = False
        vehicle.save()

        messages.success(request, _("Xóa phương tiện thành công!"))
        return redirect('parking:vehicle_list')