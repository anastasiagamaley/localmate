FROM python:3.12-slim

WORKDIR /app

COPY services/worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/shared /app/shared
COPY services/worker/ .

CMD ["celery", "-A", "worker", "worker", "--loglevel=info", "--concurrency=4"]
