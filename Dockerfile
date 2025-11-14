# Base image
FROM python:3.12-slim

# Diretório de trabalho
WORKDIR /app

# Copiar requirements e instalar dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar ffmpeg e Node.js (necessários para yt-dlp)
RUN apt-get update && \
    apt-get install -y ffmpeg nodejs curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copiar todo o restante da aplicação
COPY . .

# Criar pasta de downloads temporária caso não exista
RUN mkdir -p downloads

# Expor a porta 8080
EXPOSE 8080

# Comando para iniciar a aplicação Flask
CMD ["python", "app.py"]
