FROM python:3.12.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLCONFIGDIR=/tmp/matplotlib \
    PORT=5000

WORKDIR /app

RUN apt-get update \
    && apt-get install --no-install-recommends -y libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY start_app.py ./

RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000
CMD ["sh", "-c", "gunicorn backend.app:app --bind 0.0.0.0:${PORT} --workers 1 --threads 4 --timeout 120"]
