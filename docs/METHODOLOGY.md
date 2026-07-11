# Metodología

## 1. Pregunta de análisis

El proyecto estudia qué barrios de Valencia presentan una combinación desfavorable de vulnerabilidad urbana, capacidad de aparcamiento para bicicletas y accesibilidad espacial. El resultado es un apoyo exploratorio para priorizar revisiones, no una decisión de inversión.

## 2. Fuentes y trazabilidad

Se utilizan dos conjuntos de datos abiertos del Ayuntamiento de Valencia:

- puntos de aparcamiento de bicicleta, publicados mediante ArcGIS REST;
- polígonos de barrios con indicadores de vulnerabilidad, publicados en GeoJSON.

La descarga usa TLS verificado con el almacén de certificados del sistema. `data/raw/source_manifest.json` registra fecha de consulta, URLs, número de registros y SHA-256 de cada archivo consolidado. No se utilizan datos personales.

## 3. Coordenadas y geometrías

Los aparcamientos están en ETRS89 / UTM zona 30N (`EPSG:25830`) y se transforman a `EPSG:4326` con `pyproj`. Las operaciones point-in-polygon, validación de geometrías y puntos representativos se realizan con Shapely.

Cada aparcamiento se asigna al barrio cuya geometría lo cubre. Los registros que no intersectan ningún barrio permanecen sin asignar y no entran en los agregados por barrio.

## 4. Malla de accesibilidad

Dentro de cada barrio se genera una malla de centros de celda separados aproximadamente 300 metros. Los barrios demasiado pequeños para contener un centro de celda reciben un `representative_point` garantizado por Shapely.

Para cada punto se calcula la distancia geodésica al aparcamiento más cercano. Un punto se considera con cobertura insuficiente cuando supera 250 metros. Se resumen:

- distancia mediana;
- percentil 90 de distancia;
- proporción de puntos con cobertura insuficiente.

La distancia es en línea recta; no representa una ruta peatonal o ciclista real.

## 5. Score de prioridad

Las señales se normalizan entre 0 y 1. El escenario base combina:

- 40% presión de vulnerabilidad;
- 30% déficit de plazas por km²;
- 20% déficit de accesibilidad, medido con la distancia p90;
- 10% proporción de cobertura insuficiente.

Un score alto indica más motivos para revisar el barrio. No estima impacto causal, demanda ni retorno económico.

## 6. Sensibilidad

Se recalcula el ranking con dos escenarios alternativos:

- `equity_focus`: aumenta el peso de vulnerabilidad al 55%;
- `access_focus`: aumenta accesibilidad y cobertura insuficiente hasta un 50% combinado.

Se comparan correlación de rangos y coincidencia del top 10. En la ejecución incluida, `equity_focus` conserva 8 de los 10 primeros barrios y `access_focus` conserva 5. Esto muestra que el orden general es estable, pero las primeras posiciones dependen de la política elegida.

## 7. Ubicaciones candidatas

Los candidatos parten de puntos de malla a más de 250 metros del aparcamiento más cercano. Su score combina prioridad del barrio y déficit de distancia. Después se exige una separación mínima de 350 metros y un máximo de tres ubicaciones por barrio.

Estas coordenadas no se han validado a nivel de calle y pueden caer en zonas portuarias, industriales, privadas o físicamente inviables.

## 8. Limitaciones

- No se dispone de demanda ciclista, aforos, origen-destino ni ocupación real.
- La capacidad declarada no garantiza disponibilidad o estado de conservación.
- La densidad por superficie no corrige población, red viaria ni uso del suelo.
- Los pesos expresan una decisión analítica discutible; por eso se publica la sensibilidad.
- La distancia en línea recta ignora barreras, pendientes y cruces.
- Toda ubicación requiere inspección de calle y evaluación urbanística.

## 9. Reproducibilidad

Los datos públicos consolidados se incluyen como snapshot para ejecutar el análisis sin red. `python src/fetch_data.py` permite actualizarlos y `python src/run_pipeline.py` reconstruye tablas, figuras, sensibilidad y resumen ejecutivo. Los tests validan transformación, geometrías, malla y score.
