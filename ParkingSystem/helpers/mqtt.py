import logging
import os
import json
import paho.mqtt.client as mqtt
from django.conf import settings
from threading import Thread
import time

logger = logging.getLogger(__name__)
mqtt_client = None
mqtt_thread = None
topic_handlers = {}


def get_mqtt_client():
    global mqtt_client

    if mqtt_client and mqtt_client.is_connected():
        return mqtt_client

    try:
        mqtt_client = mqtt.Client(client_id=settings.MQTT_CLIENT_ID)
        mqtt_client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)

        mqtt_client.on_connect = on_connect
        mqtt_client.on_message = on_message
        mqtt_client.on_disconnect = on_disconnect

        mqtt_client.connect(settings.MQTT_BROKER, settings.MQTT_PORT, 60)

        return mqtt_client
    except Exception as e:
        logger.error(f"Lỗi khi tạo client MQTT: {str(e)}")
        raise


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Đã kết nối thành công tới MQTT broker")

        for topic in topic_handlers.keys():
            client.subscribe(topic)
            logger.info(f"Đã đăng ký lại topic {topic}")
    else:
        logger.error(f"Kết nối tới MQTT broker thất bại với mã lỗi {rc}")


def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode('utf-8')

    logger.debug(f"Nhận tin nhắn từ topic {topic}: {payload}")

    if topic in topic_handlers:
        try:
            try:
                payload_data = json.loads(payload)
            except json.JSONDecodeError:
                payload_data = payload

            topic_handlers[topic](topic, payload_data)
        except Exception as e:
            logger.error(f"Lỗi khi xử lý tin nhắn từ topic {topic}: {str(e)}")


def on_disconnect(client, userdata, rc):
    if rc != 0:
        logger.warning(f"Ngắt kết nối không mong muốn từ MQTT broker với mã lỗi {rc}")
        time.sleep(5)
        try:
            client.reconnect()
        except Exception as e:
            logger.error(f"Lỗi khi thử kết nối lại tới MQTT broker: {str(e)}")


def mqtt_loop():
    global mqtt_client

    try:
        mqtt_client = get_mqtt_client()
        mqtt_client.loop_forever()
    except Exception as e:
        logger.error(f"Lỗi trong vòng lặp MQTT: {str(e)}")


def start_mqtt_thread():
    global mqtt_thread

    if mqtt_thread is None or not mqtt_thread.is_alive():
        mqtt_thread = Thread(target=mqtt_loop, daemon=True)
        mqtt_thread.start()
        logger.info("Đã bắt đầu thread MQTT")


def publish_message(topic, message, qos=0, retain=False):
    try:
        client = get_mqtt_client()

        if isinstance(message, dict) or isinstance(message, list):
            message = json.dumps(message)

        if isinstance(message, str):
            message = message.encode('utf-8')
        result = client.publish(topic, message, qos, retain)

        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.debug(f"Đã gửi tin nhắn tới topic {topic}")
            return True
        else:
            logger.error(f"Lỗi khi gửi tin nhắn tới topic {topic}: {mqtt.error_string(result.rc)}")
            return False
    except Exception as e:
        logger.error(f"Lỗi khi gửi tin nhắn tới topic {topic}: {str(e)}")
        return False


def subscribe_topic(topic, handler, qos=0):
    try:
        client = get_mqtt_client()

        topic_handlers[topic] = handler

        result = client.subscribe(topic, qos)

        if result[0] == mqtt.MQTT_ERR_SUCCESS:
            logger.info(f"Đã đăng ký topic {topic} với QoS {qos}")
            return True
        else:
            logger.error(f"Lỗi khi đăng ký topic {topic}: {mqtt.error_string(result[0])}")
            return False
    except Exception as e:
        logger.error(f"Lỗi khi đăng ký topic {topic}: {str(e)}")
        return False


def unsubscribe_topic(topic):
    try:
        client = get_mqtt_client()

        if topic in topic_handlers:
            del topic_handlers[topic]

        result = client.unsubscribe(topic)

        if result[0] == mqtt.MQTT_ERR_SUCCESS:
            logger.info(f"Đã hủy đăng ký topic {topic}")
            return True
        else:
            logger.error(f"Lỗi khi hủy đăng ký topic {topic}: {mqtt.error_string(result[0])}")
            return False
    except Exception as e:
        logger.error(f"Lỗi khi hủy đăng ký topic {topic}: {str(e)}")
        return False


def disconnect_mqtt():
    global mqtt_client

    try:
        if mqtt_client and mqtt_client.is_connected():
            mqtt_client.disconnect()
            logger.info("Đã ngắt kết nối MQTT")
        return True
    except Exception as e:
        logger.error(f"Lỗi khi ngắt kết nối MQTT: {str(e)}")
        return False


try:
    start_mqtt_thread()
except Exception as e:
    logger.error(f"Không thể khởi động thread MQTT: {str(e)}")