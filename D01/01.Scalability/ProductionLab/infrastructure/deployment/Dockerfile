FROM python:3.9-alpine

WORKDIR /app

# Install system dependencies
RUN apk add --no-cache gcc musl-dev linux-headers curl

# Copy requirements from project root and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE 5000

# Use main.py as entry point
CMD ["gunicorn", "-w", "4", "--graceful-timeout", "3", "-b", "0.0.0.0:5000", "main:flask_app"]
