# Datos

El repositorio versiona snapshots de dos fuentes abiertas del Ayuntamiento de Valencia para permitir una reconstrucción sin conexión:

- `raw/bike_parking_arcgis.json`: aparcamientos de bicicleta publicados mediante ArcGIS REST.
- `raw/neighborhood_vulnerability.geojson`: barrios e indicadores agregados de vulnerabilidad.
- `raw/source_manifest.json`: URL, fecha de consulta, número de registros y SHA-256 de los snapshots.

Los archivos de `processed/` y `reports/` se reconstruyen con:

```bash
python src/run_pipeline.py
```

Para obtener una versión más reciente de las fuentes públicas:

```bash
python src/fetch_data.py
python src/run_pipeline.py
```

Los datos no contienen información personal. Las fuentes mantienen sus propias condiciones de reutilización; revísalas antes de redistribuir los snapshots.
