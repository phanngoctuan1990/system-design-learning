FROM python:3.9-alpine

WORKDIR /app
RUN apk add --no-cache gcc musl-dev linux-headers
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
# Chạy ứng dụng bằng Gunicorn (Web Server Gateway Interface)
# Gunicorn giúp mô phỏng môi trường production tốt hơn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]