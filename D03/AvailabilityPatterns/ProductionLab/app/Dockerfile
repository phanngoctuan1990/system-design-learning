FROM python:3.9-slim
WORKDIR /app
COPY . .
# Cài đặt Flask và Gunicorn
RUN pip install flask gunicorn
# Gunicorn settings: --timeout 30s để xử lý các request dài.
# CMD sử dụng Gunicorn để bind vào port 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "30", "app:app"]