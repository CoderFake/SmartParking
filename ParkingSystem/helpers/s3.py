import logging
import os
from minio import Minio
from minio.error import S3Error
from django.conf import settings
import uuid

logger = logging.getLogger(__name__)


def get_minio_client():
    try:
        minio_host = os.environ.get('MINIO_HOST', 'localhost')
        minio_port = os.environ.get('MINIO_PORT', '9000')
        minio_access_key = os.environ.get('MINIO_ACCESS_KEY', 'minioadmin')
        minio_secret_key = os.environ.get('MINIO_SECRET_KEY', 'minioadmin')

        client = Minio(
            f"{minio_host}:{minio_port}",
            access_key=minio_access_key,
            secret_key=minio_secret_key,
            secure=False
        )
        return client
    except Exception as e:
        logger.error(f"Lỗi khi tạo client Minio: {str(e)}")
        raise


def ensure_bucket_exists(client, bucket_name):
    try:
        if not client.bucket_exists(bucket_name):
            # Tạo bucket mới
            client.make_bucket(bucket_name)
            logger.info(f"Đã tạo bucket {bucket_name}")
        return True
    except S3Error as e:
        logger.error(f"Lỗi khi kiểm tra/tạo bucket {bucket_name}: {str(e)}")
        return False


def upload_file(file, bucket_name, file_name=None):
    try:
        client = get_minio_client()

        if not ensure_bucket_exists(client, bucket_name):
            return None
        if file_name is None:
            file_extension = os.path.splitext(file.name)[1] if hasattr(file, 'name') else ''
            file_name = f"{uuid.uuid4()}{file_extension}"

        content_type = getattr(file, 'content_type', 'application/octet-stream')

        if hasattr(file, 'read'):
            file_size = file.size
            client.put_object(
                bucket_name,
                file_name,
                file,
                file_size,
                content_type=content_type
            )
        else:
            client.fput_object(bucket_name, file_name, file)

        base_url = f"http://{os.environ.get('MINIO_HOST')}:{os.environ.get('MINIO_EXPORT', '9997')}"
        url = f"{base_url}/{bucket_name}/{file_name}"

        logger.info(f"Đã tải lên file {file_name} vào bucket {bucket_name}")
        return url

    except Exception as e:
        logger.error(f"Lỗi khi tải lên file vào bucket {bucket_name}: {str(e)}")
        return None


def get_file(bucket_name, file_name):
    try:
        client = get_minio_client()

        if not client.bucket_exists(bucket_name):
            logger.error(f"Bucket {bucket_name} không tồn tại")
            return None

        response = client.get_object(bucket_name, file_name)
        data = response.read()
        response.close()
        response.release_conn()

        return data

    except Exception as e:
        logger.error(f"Lỗi khi lấy file {file_name} từ bucket {bucket_name}: {str(e)}")
        return None


def delete_file(bucket_name, file_name):
    try:
        client = get_minio_client()

        if not client.bucket_exists(bucket_name):
            logger.error(f"Bucket {bucket_name} không tồn tại")
            return False

        client.remove_object(bucket_name, file_name)
        logger.info(f"Đã xóa file {file_name} từ bucket {bucket_name}")

        return True

    except Exception as e:
        logger.error(f"Lỗi khi xóa file {file_name} từ bucket {bucket_name}: {str(e)}")
        return False


def list_files(bucket_name, prefix=None):
    try:
        client = get_minio_client()

        if not client.bucket_exists(bucket_name):
            logger.error(f"Bucket {bucket_name} không tồn tại")
            return None

        objects = client.list_objects(bucket_name, prefix=prefix, recursive=True)
        result = [obj.object_name for obj in objects]

        return result

    except Exception as e:
        logger.error(f"Lỗi khi liệt kê file trong bucket {bucket_name}: {str(e)}")
        return None