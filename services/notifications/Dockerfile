FROM python:3.12-slim

WORKDIR /app

COPY services/notifications/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/notifications/ .

EXPOSE 8007

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8007", "--workers", "2"]
