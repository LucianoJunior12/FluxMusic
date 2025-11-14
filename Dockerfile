FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar ffmpeg e nodejs
RUN apt-get update && apt-get install -y ffmpeg nodejs

COPY . .

EXPOSE 8080
CMD ["python", "app.py"]
