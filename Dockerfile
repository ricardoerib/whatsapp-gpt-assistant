FROM python:3.11-slim


ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Criar diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    ffmpeg \
    libasound2-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primeiro para aproveitar o cache do Docker
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY ./app /app/app
COPY ./data /app/data

# Criar diretório para armazenar arquivos de áudio temporários
RUN mkdir -p /app/temp/audio

# Expor a porta que o aplicativo usa
EXPOSE 8000

# Comando para iniciar a aplicação
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]