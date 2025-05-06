import logging
import os
import json
import firebase_admin
from firebase_admin import credentials, auth, firestore, storage
from django.conf import settings

logger = logging.getLogger(__name__)
firebase_app = None


def initialize_firebase():
    global firebase_app

    if firebase_app:
        return firebase_app

    try:
        if not firebase_admin._apps:
            cred_dict = settings.FIREBASE_CREDENTIALS
            cred = credentials.Certificate(cred_dict)
            firebase_app = firebase_admin.initialize_app(cred, {
                'storageBucket': settings.FIREBASE_CONFIG.get('storageBucket')
            })
            logger.info("Đã khởi tạo Firebase Admin SDK")
        else:
            firebase_app = firebase_admin.get_app()

        return firebase_app
    except Exception as e:
        logger.error(f"Lỗi khi khởi tạo Firebase Admin SDK: {str(e)}")
        raise


def verify_id_token(id_token):
    try:
        initialize_firebase()
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        logger.error(f"Lỗi khi xác thực token Firebase: {str(e)}")
        return None


def get_user_info(uid):
    try:
        initialize_firebase()
        user = auth.get_user(uid)
        return {
            'uid': user.uid,
            'email': user.email,
            'display_name': user.display_name,
            'phone_number': user.phone_number,
            'photo_url': user.photo_url,
            'provider_data': [p.__dict__ for p in user.provider_data],
            'email_verified': user.email_verified
        }
    except Exception as e:
        logger.error(f"Lỗi khi lấy thông tin người dùng Firebase {uid}: {str(e)}")
        return None


def create_firebase_user(email, password, display_name=None, phone_number=None):
    try:
        initialize_firebase()
        user = auth.create_user(
            email=email,
            password=password,
            display_name=display_name,
            phone_number=phone_number
        )
        return {
            'uid': user.uid,
            'email': user.email,
            'display_name': user.display_name
        }
    except Exception as e:
        logger.error(f"Lỗi khi tạo người dùng Firebase: {str(e)}")
        return None


def update_firebase_user(uid, **kwargs):
    try:
        initialize_firebase()
        user = auth.update_user(uid, **kwargs)
        return {
            'uid': user.uid,
            'email': user.email,
            'display_name': user.display_name,
            'phone_number': user.phone_number,
            'photo_url': user.photo_url
        }
    except Exception as e:
        logger.error(f"Lỗi khi cập nhật người dùng Firebase {uid}: {str(e)}")
        return None


def delete_firebase_user(uid):
    try:
        initialize_firebase()
        auth.delete_user(uid)
        logger.info(f"Đã xóa người dùng Firebase {uid}")
        return True
    except Exception as e:
        logger.error(f"Lỗi khi xóa người dùng Firebase {uid}: {str(e)}")
        return False


def upload_to_firebase_storage(file, path):
    try:
        initialize_firebase()
        bucket = storage.bucket()
        blob = bucket.blob(path)

        if hasattr(file, 'read'):
            blob.upload_from_file(file)
        else:
            blob.upload_from_filename(file)

        blob.make_public()
        url = blob.public_url

        logger.info(f"Đã tải lên file lên Firebase Storage: {path}")
        return url
    except Exception as e:
        logger.error(f"Lỗi khi tải lên file lên Firebase Storage: {str(e)}")
        return None


def get_firestore_client():
    try:
        initialize_firebase()
        return firestore.client()
    except Exception as e:
        logger.error(f"Lỗi khi lấy client Firestore: {str(e)}")
        raise


def save_document(collection, document_id, data):
    try:
        db = get_firestore_client()
        db.collection(collection).document(document_id).set(data)
        logger.info(f"Đã lưu document {document_id} vào collection {collection}")
        return True
    except Exception as e:
        logger.error(f"Lỗi khi lưu document vào Firestore: {str(e)}")
        return False


def get_document(collection, document_id):
    try:
        db = get_firestore_client()
        doc_ref = db.collection(collection).document(document_id)
        doc = doc_ref.get()

        if doc.exists:
            return doc.to_dict()
        else:
            logger.warning(f"Document {document_id} không tồn tại trong collection {collection}")
            return None
    except Exception as e:
        logger.error(f"Lỗi khi lấy document từ Firestore: {str(e)}")
        return None


def update_document(collection, document_id, data):
    try:
        db = get_firestore_client()
        db.collection(collection).document(document_id).update(data)
        logger.info(f"Đã cập nhật document {document_id} trong collection {collection}")
        return True
    except Exception as e:
        logger.error(f"Lỗi khi cập nhật document trong Firestore: {str(e)}")
        return False


def delete_document(collection, document_id):
    try:
        db = get_firestore_client()
        db.collection(collection).document(document_id).delete()
        logger.info(f"Đã xóa document {document_id} khỏi collection {collection}")
        return True
    except Exception as e:
        logger.error(f"Lỗi khi xóa document khỏi Firestore: {str(e)}")
        return False


def query_documents(collection, filters=None, order_by=None, limit=None):
    try:
        db = get_firestore_client()
        query = db.collection(collection)

        if filters:
            for field, op, value in filters:
                query = query.where(field, op, value)

        if order_by:
            field, direction = order_by
            if direction == 'desc':
                query = query.order_by(field, direction=firestore.Query.DESCENDING)
            else:
                query = query.order_by(field)

        if limit:
            query = query.limit(limit)

        docs = query.stream()
        result = []

        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            result.append(data)

        return result
    except Exception as e:
        logger.error(f"Lỗi khi truy vấn documents từ Firestore: {str(e)}")
        return None