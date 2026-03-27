FROM python:3.12-slim

WORKDIR /app

COPY services/users/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/shared /app/shared
COPY services/users/ .

EXPOSE 8002

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "4"]
