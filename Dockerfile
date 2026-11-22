FROM python:3.13-slim

WORKDIR /app

COPY MainCompiler.py .
COPY Token.py .
COPY Sintactico.py .
COPY TokenizarFechas.py .
COPY GestorReglas.py .
COPY reglas.json .
COPY Servidor.py .
COPY GeneradorPDF.py .
COPY requirements.txt .

COPY frontend ./frontend

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

# Usamos "sh -c" para poder leer la variable de entorno $PORT en tiempo de
# ejecución. En Render/Railway, la plataforma inyecta su propio $PORT y el
# contenedor DEBE escuchar ahí, o el health check falla. En local (docker
# compose, sin $PORT definido) cae al 8000 de siempre.
CMD ["sh", "-c", "uvicorn Servidor:app --host 0.0.0.0 --port ${PORT:-8000}"]