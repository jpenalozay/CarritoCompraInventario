FROM python:3.9-slim

WORKDIR /app

# Crear directorio data
RUN mkdir -p /app/data

# Copiar archivos necesarios
COPY requirements.txt .
COPY producer/ producer/
COPY schemas/ schemas/
COPY data/ data/

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Comando por defecto
CMD ["python", "-u", "producer/transaction_producer.py"] 