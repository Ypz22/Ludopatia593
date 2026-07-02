FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# deps primero (capa cacheable)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY data ./data
COPY start.sh ./start.sh
RUN chmod +x start.sh

# Entrenar modelo en build time para que el arranque sea inmediato
RUN python -m app.ml.train

# usuario no-root (mínimo privilegio)
RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 8000
CMD ["./start.sh"]
