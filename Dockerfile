FROM python:3.11-slim

WORKDIR /app

COPY main.py /app/
COPY .env.example /app/

ENV PYTHONUNBUFFERED=1 \
    PORT=8790

EXPOSE 8790

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8790/health')" || exit 1

CMD ["python3", "main.py"]
