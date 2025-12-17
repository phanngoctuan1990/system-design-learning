FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Gunicorn sẽ đọc biến môi trường GUNICORN_WORKERS để cấu hình worker count
CMD gunicorn -w $GUNICORN_WORKERS -b 0.0.0.0:8000 app:app