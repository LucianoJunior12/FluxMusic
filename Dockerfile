FROM python:3.11-slim

# Instala FFmpeg (essencial pra conversão áudio)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p downloads

# Usa gunicorn pra prod (melhor que dev server)
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
