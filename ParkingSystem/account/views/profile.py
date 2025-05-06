from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import gettext_lazy as _
from account.models import Profile
from helpers.s3 import upload_file


class ProfileView(LoginRequiredMixin, View):
    """View hiển thị thông tin hồ sơ người dùng"""

    def get(self, request):
        user = request.user
        try:
            profile = user.profile
        except Profile.DoesNotExist:
            profile = Profile.objects.create(user=user)

        context = {
            'user': user,
            'profile': profile,
        }

        return render(request, 'app/account/profile.html', context)


class UpdateProfileView(LoginRequiredMixin, View):
    """View cập nhật thông tin hồ sơ người dùng"""

    def post(self, request):
        user = request.user
        try:
            profile = user.profile
        except Profile.DoesNotExist:
            profile = Profile.objects.create(user=user)

        user.username = request.POST.get('username', user.username)
        user.phone_number = request.POST.get('phone_number', user.phone_number)
        user.save()

        profile.full_name = request.POST.get('full_name', profile.full_name)
        profile.address = request.POST.get('address', profile.address)

        date_of_birth = request.POST.get('date_of_birth')
        if date_of_birth:
            profile.date_of_birth = date_of_birth

        avatar = request.FILES.get('avatar')
        if avatar:
            try:
                avatar_url = upload_file(
                    file=avatar,
                    bucket_name='parking-avatars',
                    file_name=f'avatar_{user.id}_{avatar.name}'
                )
                profile.avatar = avatar_url
            except Exception as e:
                messages.error(request, _("Không thể tải lên ảnh đại diện. Lỗi: {}").format(str(e)))

        profile.save()
        messages.success(request, _("Cập nhật hồ sơ thành công!"))

        return redirect('account:profile')