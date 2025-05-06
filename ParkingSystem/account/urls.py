from django.urls import path
from account.views.sigup_login import (
    SignupView, LoginView, LogoutView,
    ForgotPasswordView, ResetPasswordView,
    VerifyEmailView
)
from account.views.profile import ProfileView, UpdateProfileView

app_name = 'account'

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # Xác nhận email
    path('verify-email/<str:token>/', VerifyEmailView.as_view(), name='verify_email'),

    # Quên mật khẩu
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('reset-password/<str:token>/', ResetPasswordView.as_view(), name='reset_password'),

    # Hồ sơ người dùng
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/update/', UpdateProfileView.as_view(), name='update_profile'),
]