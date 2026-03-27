FROM python:3.12-slim

WORKDIR /app

COPY services/search/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/shared /app/shared
COPY services/search/ .

EXPOSE 8003

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003", "--workers", "2"]
