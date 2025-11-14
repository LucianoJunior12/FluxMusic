FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN adduser --disabled-password --gecos '' appuser && \
    mkdir -p downloads && \
    chown -R appuser:appuser /app
USER appuser

COPY --chown=appuser:appuser . .

EXPOSE 8080
CMD ["python", "app.py"]
