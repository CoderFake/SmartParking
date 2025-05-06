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

# Thực hiện migrations
cd /app/ParkingSystem
python manage.py makemigrations
python manage.py migrate --noinput

# Tạo superuser và site
python create_superuser_and_site.py

# Thu thập static files
python manage.py collectstatic --noinput

# Chạy server
exec gunicorn ParkingSystem.wsgi:application --bind 0.0.0.0:8000 --workers 4 --threads 2