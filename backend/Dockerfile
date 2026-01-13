FROM python:3.14-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip && \
    python -m pip install --no-cache-dir -r /app/requirements.txt

RUN adduser --disabled-password --gecos "" appuser || true && chown -R appuser:appuser /app

COPY . /app

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

USER appuser

CMD ["uvicorn", "app.v1.server.server:app", "--host", "0.0.0.0", "--port", "8000"]