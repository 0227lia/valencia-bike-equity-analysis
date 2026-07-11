# Datos

El repositorio incluye snapshots de dos fuentes públicas del Ayuntamiento de Valencia para que el análisis pueda reproducirse sin depender de la red.

- Aparcamientos de bicicleta: `data/raw/bike_parking_arcgis.json`.
- Vulnerabilidad por barrios: `data/raw/neighborhood_vulnerability.geojson`.
- Trazabilidad y hashes: `data/raw/source_manifest.json`.

Los archivos de `data/processed/` se generan mediante `python src/run_pipeline.py`. Para actualizar las fuentes:

```bash
python src/fetch_data.py
python src/run_pipeline.py
```

Antes de redistribuir los datos fuera de este repositorio se deben revisar las condiciones publicadas en las páginas originales del portal de datos abiertos.
