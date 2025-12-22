# Script cấu hình Slave, sử dụng pg_basebackup để lấy snapshot từ Master và thiết lập chế độ phục hồi.
#!/bin/bash
set -e

# Đợi Master sẵn sàng
until PGPASSWORD="password" pg_isready -h db-master -U admin -d appdb
do
  echo "Waiting for Master to be ready..."
  sleep 2
done

echo "Starting Slave setup..."

# Kiểm tra xem đã setup chưa (nếu có standby.signal thì skip)
if [ -f /var/lib/postgresql/data/standby.signal ]; then
  echo "Slave already configured. Skipping setup."
  exec postgres
fi

# Stop PostgreSQL nếu đang chạy
pg_ctl -D /var/lib/postgresql/data stop || true

# 1. Xóa dữ liệu cũ và thực hiện base backup từ Master
rm -rf /var/lib/postgresql/data/*
PGPASSWORD="repl_password" pg_basebackup -h db-master -U repl_user -D /var/lib/postgresql/data -P -R -w

# 2. Tạo recovery signal file (cho Postgres 12+)
touch /var/lib/postgresql/data/standby.signal

echo "Slave setup complete. Starting PostgreSQL in recovery mode."

# 3. Start PostgreSQL
exec postgres