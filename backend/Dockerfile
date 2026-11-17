FROM python:3.12-slim
WORKDIR /srv
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
# Bookings are short and DB-bound: sync workers with threads. Scale by
# configuration, not code (docs/SCALING.md).
ENV WEB_CONCURRENCY=2 THREADS=4
# Migrate, seed only if empty, then serve.
CMD alembic upgrade head \
 && flask --app app seed \
 && gunicorn "app:create_app()" --bind 0.0.0.0:8000 \
      --workers "$WEB_CONCURRENCY" --threads "$THREADS"
