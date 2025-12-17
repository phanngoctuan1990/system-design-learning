FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Chạy ứng dụng bằng Gunicorn, sử dụng biến môi trường để giới hạn số worker
CMD gunicorn -w $GUNICORN_WORKERS -b 0.0.0.0:8000 app:app
