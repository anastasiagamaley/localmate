FROM python:3.12-slim

WORKDIR /app

# Install deps first (layer cache)
COPY services/auth/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared lib
COPY services/shared /app/shared

# Copy service code
COPY services/auth/ .

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "4"]
