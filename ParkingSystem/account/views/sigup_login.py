from django.shortcuts import render, redirect
from django.views import View
from django.urls import reverse
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sites.models import Site
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone
import jwt
from datetime import datetime, timedelta

from account.models import User, Profile
from helpers.send_mail import send_verification_email, send_reset_password_email


class SignupView(View):
    """View xử lý đăng ký người dùng mới"""

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        return render(request, 'app/account/signup.html')

    def post(self, request):
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if not email or not username or not password:
            messages.error(request, _("Vui lòng điền đầy đủ thông tin"))
            return render(request, 'app/account/signup.html')

        if password != confirm_password:
            messages.error(request, _("Mật khẩu không khớp"))
            return render(request, 'app/account/signup.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, _("Email đã được sử dụng"))
            return render(request, 'app/account/signup.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, _("Tên đăng nhập đã được sử dụng"))
            return render(request, 'app/account/signup.html')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            status='pending',
            user_type='customer'
        )

        Profile.objects.create(user=user)

        token_data = {
            'user_id': user.id,
            'email': user.email,
            'exp': timezone.now() + timedelta(days=1)
        }

        token = jwt.encode(token_data, settings.SECRET_KEY, algorithm='HS256')

        site = Site.objects.get(id=settings.SITE_ID)
        verification_url = f"{request.scheme}://{site.domain}{reverse('account:verify_email', kwargs={'token': token})}"

        try:
            send_verification_email(user.email, verification_url)
            messages.success(request, _("Đăng ký thành công! Vui lòng kiểm tra email để xác nhận tài khoản"))
        except Exception as e:
            messages.warning(request,
                             _("Đăng ký thành công nhưng không thể gửi email xác nhận. Vui lòng liên hệ quản trị viên."))

        return redirect('account:login')


class VerifyEmailView(View):
    """View xử lý xác nhận email"""

    def get(self, request, token):
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user_id = payload.get('user_id')

            user = User.objects.get(id=user_id)

            user.status = 'active'
            user.save()

            messages.success(request, _("Xác nhận email thành công! Bạn có thể đăng nhập ngay bây giờ."))
            return redirect('account:login')

        except jwt.ExpiredSignatureError:
            messages.error(request, _("Liên kết xác nhận đã hết hạn."))
        except (jwt.InvalidTokenError, User.DoesNotExist):
            messages.error(request, _("Liên kết xác nhận không hợp lệ."))

        return redirect('account:login')


class LoginView(View):
    """View xử lý đăng nhập"""

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        return render(request, 'app/account/login.html')

    def post(self, request):
        email = request.POST.get('email')
        password = request.POST.get('password')

        if not email or not password:
            messages.error(request, _("Vui lòng điền đầy đủ thông tin"))
            return render(request, 'app/account/login.html')

        user = authenticate(request, email=email, password=password)

        if user is not None:
            if user.status == 'active':
                login(request, user)
                next_url = request.GET.get('next', 'home')
                return redirect(next_url)
            elif user.status == 'pending':
                messages.warning(request, _("Tài khoản chưa được xác nhận. Vui lòng kiểm tra email để xác nhận."))
            elif user.status == 'blocked':
                messages.error(request, _("Tài khoản đã bị khóa. Vui lòng liên hệ quản trị viên."))
            else:
                messages.error(request, _("Tài khoản không hoạt động."))
        else:
            messages.error(request, _("Email hoặc mật khẩu không chính xác"))

        return render(request, 'app/account/login.html')


class LogoutView(LoginRequiredMixin, View):
    """View xử lý đăng xuất"""

    def get(self, request):
        logout(request)
        messages.success(request, _("Đăng xuất thành công!"))
        return redirect('home')


class ForgotPasswordView(View):
    """View xử lý quên mật khẩu"""

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        return render(request, 'app/account/forgot_password.html')

    def post(self, request):
        email = request.POST.get('email')

        if not email:
            messages.error(request, _("Vui lòng nhập địa chỉ email"))
            return render(request, 'app/account/forgot_password.html')

        try:
            user = User.objects.get(email=email)

            token_data = {
                'user_id': user.id,
                'email': user.email,
                'exp': datetime.utcnow() + timedelta(hours=1)
            }

            token = jwt.encode(token_data, settings.SECRET_KEY, algorithm='HS256')

            site = Site.objects.get(id=settings.SITE_ID)
            reset_url = f"{request.scheme}://{site.domain}{reverse('account:reset_password', kwargs={'token': token})}"

            send_reset_password_email(user.email, reset_url)
            messages.success(request, _("Một email hướng dẫn đặt lại mật khẩu đã được gửi đến địa chỉ email của bạn."))

        except User.DoesNotExist:
            messages.success(request,
                             _("Nếu địa chỉ email tồn tại trong hệ thống, bạn sẽ nhận được email hướng dẫn đặt lại mật khẩu."))

        return redirect('account:login')


class ResetPasswordView(View):
    """View xử lý đặt lại mật khẩu"""

    def get(self, request, token):
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            return render(request, 'app/account/reset_password.html', {'token': token})

        except jwt.ExpiredSignatureError:
            messages.error(request, _("Liên kết đặt lại mật khẩu đã hết hạn."))
        except jwt.InvalidTokenError:
            messages.error(request, _("Liên kết đặt lại mật khẩu không hợp lệ."))

        return redirect('account:login')

    def post(self, request, token):
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not new_password or not confirm_password:
            messages.error(request, _("Vui lòng điền đầy đủ thông tin"))
            return render(request, 'app/account/reset_password.html', {'token': token})

        if new_password != confirm_password:
            messages.error(request, _("Mật khẩu không khớp"))
            return render(request, 'app/account/reset_password.html', {'token': token})

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user_id = payload.get('user_id')

            user = User.objects.get(id=user_id)

            user.set_password(new_password)
            user.save()

            messages.success(request, _("Đặt lại mật khẩu thành công! Bạn có thể đăng nhập với mật khẩu mới."))
            return redirect('account:login')

        except jwt.ExpiredSignatureError:
            messages.error(request, _("Liên kết đặt lại mật khẩu đã hết hạn."))
        except (jwt.InvalidTokenError, User.DoesNotExist):
            messages.error(request, _("Liên kết đặt lại mật khẩu không hợp lệ."))

        return redirect('account:login')