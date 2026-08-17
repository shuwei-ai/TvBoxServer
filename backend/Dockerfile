FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SERVER_PORT=8000

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py langchain_agent.py ./
COPY app ./app
COPY static ./static

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.getenv('SERVER_PORT', '8000') + '/', timeout=2)"

CMD ["sh", "-c", "exec uvicorn server:app --host 0.0.0.0 --port \"${SERVER_PORT:-8000}\""]
