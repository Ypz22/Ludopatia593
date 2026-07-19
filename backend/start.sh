#!/bin/sh
set -e

# Espera a que PostgreSQL acepte conexiones (máx 60 s)
echo "Esperando base de datos..."
MAX=30
i=0
until python -c "
import os, sys
url = os.getenv('DATABASE_URL', '')
if not url:
    sys.exit(1)
import psycopg2, re
# Extraer host/port/dbname/user/password de la URL
m = re.match(r'postgres(?:ql)?(?:\+psycopg2)?://([^:]+):([^@]+)@([^:/]+):?(\d+)?/(.+)', url)
if not m:
    sys.exit(1)
user, pw, host, port, db = m.groups()
psycopg2.connect(host=host, port=int(port or 5432), dbname=db, user=user, password=pw).close()
" 2>/dev/null; do
    i=$((i+1))
    if [ $i -ge $MAX ]; then
        echo "ERROR: no se pudo conectar a la base de datos después de ${MAX} intentos"
        exit 1
    fi
    echo "  intento $i/$MAX — reintentando en 2 s..."
    sleep 2
done

echo "Base de datos lista. Ejecutando seed..."
# Entrena el modelo solo si aún no existe (data/model.json). En compose la
# carpeta data es un volumen persistente: el primer arranque entrena, los
# siguientes lo reutilizan -> reinicios rápidos y menos ventana de "backend no
# disponible" en el frontend. Fuerza reentrenar con RETRAIN=1.
if [ "${RETRAIN:-0}" = "1" ] || [ ! -f data/model.json ]; then
  python -m app.ml.train
fi
python -m app.seed
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --no-server-header
