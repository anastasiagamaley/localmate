FROM python:3.12-slim

WORKDIR /app

COPY services/gigs/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/shared /app/shared
COPY services/gigs/ .

EXPOSE 8006

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8006", "--workers", "4"]
