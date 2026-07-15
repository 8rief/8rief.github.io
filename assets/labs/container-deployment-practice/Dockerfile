FROM python:3.14-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PORT=8080 \
    DATA_DIR=/data \
    APP_NAME=container-lab

COPY app/server.py /app/server.py

RUN useradd --uid 10001 --create-home --shell /usr/sbin/nologin appuser \
    && mkdir -p /data \
    && chown -R appuser:appuser /data /app

USER appuser
EXPOSE 8080
HEALTHCHECK --interval=5s --timeout=2s --retries=5 CMD python -c "import json,urllib.request; r=urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=2); data=json.loads(r.read().decode()); raise SystemExit(0 if data.get('status') == 'ok' else 1)"
CMD ["python", "/app/server.py"]
