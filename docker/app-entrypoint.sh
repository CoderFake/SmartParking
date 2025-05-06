#!/bin/bash

set -e

function postgres_ready(){
python << END
import sys
import psycopg2
import os

try:
    dbname = os.environ.get('POSTGRES_DB')
    user = os.environ.get('POSTGRES_USER')
    password = os.environ.get('POSTGRES_PASSWORD')
    host = os.environ.get('POSTGRES_HOST')
    port = os.environ.get('POSTGRES_PORT')

    conn = psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port
    )
except psycopg2.OperationalError:
    sys.exit(-1)
sys.exit(0)
END
}


function mqtt_ready(){
python << END
import sys
import paho.mqtt.client as mqtt
import os
import time

try:
    broker = os.environ.get('MQTT_BROKER')
    port = int(os.environ.get('MQTT_PORT'))
    username = os.environ.get('MQTT_USERNAME')
    password = os.environ.get('MQTT_PASSWORD')
    client_id = os.environ.get('MQTT_CLIENT_ID')

    client = mqtt.Client(client_id)
    client.username_pw_set(username, password)
    client.connect(broker, port, 60)
    client.disconnect()
except Exception:
    sys.exit(-1)
sys.exit(0)
END
}

function minio_ready(){
python << END
import sys
from minio import Minio
import os

try:
    minio_host = os.environ.get('MINIO_HOST', 'minio')
    minio_port = os.environ.get('MINIO_PORT', '9000')
    minio_access_key = os.environ.get('MINIO_ACCESS_KEY', 'minioadmin')
    minio_secret_key = os.environ.get('MINIO_SECRET_KEY', 'minioadmin')

    client = Minio(
        f"{minio_host}:{minio_port}",
        access_key=minio_access_key,
        secret_key=minio_secret_key,
        secure=False
    )

    buckets = client.list_buckets()
except Exception:
    sys.exit(-1)
sys.exit(0)
END
}

until postgres_ready; do
  >&2 echo "PostgreSQL đang khởi động - đợi trong 1 giây..."
  sleep 1
done
>&2 echo "PostgreSQL đã sẵn sàng!"

until mqtt_ready; do
  >&2 echo "MQTT đang khởi động - đợi trong 1 giây..."
  sleep 1
done
>&2 echo "MQTT đã sẵn sàng!"

until minio_ready; do
  >&2 echo "Minio đang khởi động - đợi trong 1 giây..."
  sleep 1
done
>&2 echo "Minio đã sẵn sàng!"


cd /app/ParkingSystem
python manage.py makemigrations
python manage.py migrate --noinput

python create_superuser_and_site.py

python manage.py collectstatic --noinput

exec gunicorn ParkingSystem.wsgi:application --bind 0.0.0.0:8000 --workers 4 --threads 2