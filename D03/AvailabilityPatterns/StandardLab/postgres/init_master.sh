# Script cấu hình Master cho phép kết nối replication từ Slave.

#!/bin/bash
set -e

# Đợi DB khởi động hoàn toàn
until pg_isready -U admin -d appdb
do
  sleep 1
done

echo "Setting up Master configuration..."

# 1. Kích hoạt Replication và tạo user replication
# Chỉ định level log để replication
# Số lượng connection replication
# Cho phép Slave kết nối
# Tạo user replication
# Tạo table
# Insert record
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    ALTER SYSTEM SET wal_level = replica; 
    ALTER SYSTEM SET max_wal_senders = 10;
    ALTER SYSTEM SET listen_addresses = '*';
    CREATE USER repl_user WITH REPLICATION ENCRYPTED PASSWORD 'repl_password';
    CREATE TABLE IF NOT EXISTS transactions (id SERIAL PRIMARY KEY, value VARCHAR(255), timestamp TIMESTAMP DEFAULT NOW());
    INSERT INTO transactions (value) VALUES ('Initial record on Master');
EOSQL

echo "Master configuration complete. Restarting for config application."

# 2. Cấu hình pg_hba.conf để cho phép slave kết nối
echo "host replication repl_user all trust" >> /var/lib/postgresql/data/pg_hba.conf

pg_ctl reload

echo "Master is ready."
