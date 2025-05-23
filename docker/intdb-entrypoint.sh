#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    SELECT 'Đã tạo extension uuid-ossp!';
EOSQL

echo "Database đã được khởi tạo thành công!"