import hashlib
import hmac
import datetime
import os
import logging
import requests
from django.utils import timezone

logger = logging.getLogger(__name__)


def get_vnpay_config():
    return {
        'vnp_Version': '2.1.0',
        'vnp_TmnCode': os.environ.get('VNPAY_TMN_CODE', ''),
        'vnp_HashSecret': os.environ.get('VNPAY_HASH_SECRET', ''),
        'vnp_Url': os.environ.get('VNPAY_URL', 'https://sandbox.vnpayment.vn/paymentv2/vpcpay.html'),
        'vnp_ReturnUrl': '',
    }


def vnpay_create_payment_url(request, order_id, amount, order_desc, return_url):
    vnp_config = get_vnpay_config()

    vnp_params = {
        'vnp_Version': vnp_config['vnp_Version'],
        'vnp_Command': 'pay',
        'vnp_TmnCode': vnp_config['vnp_TmnCode'],
        'vnp_Amount': amount * 100,

        'vnp_CurrCode': 'VND',
        'vnp_TxnRef': order_id,
        'vnp_OrderInfo': order_desc,
        'vnp_OrderType': 'billpayment',
        'vnp_Locale': 'vn',
        'vnp_ReturnUrl': return_url,
        'vnp_IpAddr':  request.META.get('REMOTE_ADDR', '127.0.0.1'),
        'vnp_CreateDate': datetime.datetime.now().strftime('%Y%m%d%H%M%S'),
    }

    sorted_params = sorted(vnp_params.items())

    query_string = ''
    for key, value in sorted_params:
        if query_string:
            query_string += '&' + key + '=' + str(value)
        else:
            query_string = key + '=' + str(value)

    hmac_signature = hmac.new(
        vnp_config['vnp_HashSecret'].encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha512
    ).hexdigest()

    query_string += '&vnp_SecureHash=' + hmac_signature

    payment_url = vnp_config['vnp_Url'] + '?' + query_string

    logger.info(f"Đã tạo URL thanh toán VNPay cho đơn hàng {order_id}")

    return payment_url


def vnpay_verify_payment(vnp_params):
    vnp_config = get_vnpay_config()

    if 'vnp_SecureHash' not in vnp_params:
        return False

    vnp_secure_hash = vnp_params['vnp_SecureHash']
    vnp_data = dict(vnp_params)
    del vnp_data['vnp_SecureHash']

    sorted_params = sorted(vnp_data.items())

    query_string = ''
    for key, value in sorted_params:
        if query_string:
            query_string += '&' + key + '=' + str(value)
        else:
            query_string = key + '=' + str(value)

    hmac_signature = hmac.new(
        vnp_config['vnp_HashSecret'].encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha512
    ).hexdigest()

    if vnp_secure_hash == hmac_signature:
        if vnp_params.get('vnp_ResponseCode') == '00':
            return True

    return False


def vnpay_query_transaction(order_id, transaction_date):
    vnp_config = get_vnpay_config()

    vnp_params = {
        'vnp_Version': vnp_config['vnp_Version'],
        'vnp_Command': 'querydr',
        'vnp_TmnCode': vnp_config['vnp_TmnCode'],
        'vnp_TxnRef': order_id,
        'vnp_OrderInfo': f'Query transaction {order_id}',
        'vnp_TransactionDate': transaction_date,
        'vnp_CreateDate': timezone.now().strftime('%Y%m%d%H%M%S'),
        'vnp_IpAddr': '127.0.0.1',
    }

    sorted_params = sorted(vnp_params.items())

    query_string = ''
    for key, value in sorted_params:
        if query_string:
            query_string += '&' + key + '=' + str(value)
        else:
            query_string = key + '=' + str(value)

    hmac_signature = hmac.new(
        vnp_config['vnp_HashSecret'].encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha512
    ).hexdigest()

    vnp_params['vnp_SecureHash'] = hmac_signature

    query_url = 'https://sandbox.vnpayment.vn/merchant_webapi/api/transaction'

    try:
        response = requests.post(query_url, json=vnp_params)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logger.error(f"Lỗi khi truy vấn giao dịch VNPay: {str(e)}")

    return None


def vnpay_refund(order_id, transaction_date, amount, transaction_type='02'):
    vnp_config = get_vnpay_config()

    vnp_params = {
        'vnp_Version': vnp_config['vnp_Version'],
        'vnp_Command': 'refund',
        'vnp_TmnCode': vnp_config['vnp_TmnCode'],
        'vnp_TxnRef': order_id,
        'vnp_Amount': amount * 100,
        'vnp_OrderInfo': f'Refund transaction {order_id}',
        'vnp_TransactionDate': transaction_date,
        'vnp_CreateDate': datetime.datetime.now().strftime('%Y%m%d%H%M%S'),
        'vnp_IpAddr': '127.0.0.1',
        'vnp_TransactionType': transaction_type,
    }

    sorted_params = sorted(vnp_params.items())

    query_string = ''
    for key, value in sorted_params:
        if query_string:
            query_string += '&' + key + '=' + str(value)
        else:
            query_string = key + '=' + str(value)

    hmac_signature = hmac.new(
        vnp_config['vnp_HashSecret'].encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha512
    ).hexdigest()

    vnp_params['vnp_SecureHash'] = hmac_signature

    refund_url = 'https://sandbox.vnpayment.vn/merchant_webapi/api/transaction'

    try:
        response = requests.post(refund_url, json=vnp_params)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logger.error(f"Lỗi khi hoàn tiền giao dịch VNPay: {str(e)}")

    return None