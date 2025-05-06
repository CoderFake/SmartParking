import logging
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

logger = logging.getLogger(__name__)


def send_email(subject, to_email, html_content, text_content=None):
    if text_content is None:
        text_content = strip_tags(html_content)

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.EMAIL_HOST_USER,
            to=[to_email]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        logger.info(f"Đã gửi email '{subject}' tới {to_email}")
        return True
    except Exception as e:
        logger.error(f"Lỗi khi gửi email tới {to_email}: {str(e)}")
        return False


def send_verification_email(email, verification_url):
    subject = "Xác nhận đăng ký tài khoản - Hệ thống đỗ xe thông minh"
    html_content = render_to_string(
        'app/email/verification_email.html',
        {
            'verification_url': verification_url
        }
    )

    return send_email(subject, email, html_content)


def send_reset_password_email(email, reset_url):
    subject = "Đặt lại mật khẩu - Hệ thống đỗ xe thông minh"
    html_content = render_to_string(
        'app/email/reset_password_email.html',
        {
            'reset_url': reset_url
        }
    )

    return send_email(subject, email, html_content)


def send_parking_notification(email, parking_session):
    subject = "Thông báo đỗ xe - Hệ thống đỗ xe thông minh"
    html_content = render_to_string(
        'app/email/parking_notification.html',
        {
            'parking_session': parking_session
        }
    )

    return send_email(subject, email, html_content)


def send_payment_confirmation(email, payment):
    """
    Gửi xác nhận thanh toán thành công

    Args:
        email (str): Địa chỉ email người dùng
        payment (Payment): Thông tin thanh toán

    Returns:
        bool: True nếu gửi thành công, False nếu có lỗi
    """
    subject = "Xác nhận thanh toán - Hệ thống đỗ xe thông minh"
    html_content = render_to_string(
        'app/email/payment_confirmation.html',
        {
            'payment': payment
        }
    )

    return send_email(subject, email, html_content)


def send_ticket_receipt(email, ticket):

    subject = "Biên lai vé đỗ xe - Hệ thống đỗ xe thông minh"
    html_content = render_to_string(
        'app/email/ticket_receipt.html',
        {
            'ticket': ticket
        }
    )

    return send_email(subject, email, html_content)