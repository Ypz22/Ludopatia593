#!/bin/sh
set -e
# Entrena el modelo solo si aún no existe (data/model.json). En compose la
# carpeta data es un volumen persistente: el primer arranque entrena, los
# siguientes lo reutilizan -> reinicios rápidos y menos ventana de "backend no
# disponible" en el frontend. Fuerza reentrenar con RETRAIN=1.
if [ "${RETRAIN:-0}" = "1" ] || [ ! -f data/model.json ]; then
  python -m app.ml.train
fi
python -m app.seed
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --no-server-header
