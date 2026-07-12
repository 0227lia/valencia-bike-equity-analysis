# Metodología

## 1. Propósito y unidad de análisis

El proyecto identifica señales territoriales que justifican una revisión adicional de la red de aparcamiento de bicicletas. La unidad principal es el barrio municipal (`codbar`); la unidad operativa de accesibilidad es un punto interior de malla. No es un modelo de demanda ni un sistema de decisión automática.

## 2. Fuentes, privacidad y trazabilidad

Se usan dos fuentes abiertas del Ayuntamiento de Valencia:

- puntos de aparcamiento de bicicleta publicados mediante ArcGIS REST;
- polígonos de barrios e indicadores de vulnerabilidad publicados como GeoJSON.

No se procesan datos personales. La descarga usa TLS verificado con `truststore`. El archivo `data/raw/source_manifest.json` registra URL, fecha de consulta, número de registros y hash SHA-256 de cada snapshot.

## 3. Normalización espacial

Los puntos de aparcamiento se publican en ETRS89 / UTM 30N (`EPSG:25830`) y se transforman a `EPSG:4326` con `pyproj`. Las geometrías se validan con Shapely y cada punto se asigna al polígono de barrio que lo cubre. Los puntos no asignados quedan fuera de los agregados por barrio.

## 4. Accesibilidad

Se construyen dos mallas de centros de celda dentro de cada geometría de barrio:

| Uso | Separación aproximada | Propósito |
|---|---:|---|
| Diagnóstico | 300 m | Resumen comparable por barrio. |
| Simulación | 150 m | Reducir el efecto de discretización en el cribado de áreas. |

Para cada punto se calcula la distancia geodésica al aparcamiento existente más cercano. Un punto queda por encima del umbral si supera 250 m. La métrica es una aproximación de línea recta, no una ruta peatonal o ciclista.

## 5. Modelo multicriterio base

Las señales se normalizan mediante min-max a `[0, 1]`; un valor alto significa mayor motivo de revisión:

| Componente | Señal | Peso base |
|---|---|---:|
| Presión de vulnerabilidad | `ind_global` invertido | 0,40 |
| Déficit de capacidad | plazas declaradas por km² invertidas | 0,30 |
| Déficit de accesibilidad | percentil 90 de la distancia | 0,20 |
| Cobertura insuficiente | proporción de malla por encima de 250 m | 0,10 |

El score es una suma ponderada. No interpreta el índice de vulnerabilidad como una variable causal ni estima necesidad individual.

## 6. Sensibilidad y robustez de pesos

Primero se comparan tres escenarios explícitos: `default`, `equity_focus` y `access_focus`. Se publican correlación de rangos y solapamiento del top 10.

Después se ejecutan 10.000 muestras de una distribución Dirichlet con parámetros `45 * pesos_base` y semilla 42. La concentración 45 mantiene las muestras alrededor de los pesos declarados, pero permite variación de política. Para cada barrio se informa de:

- score esperado e intervalo percentil 5-95;
- rango esperado e intervalo percentil 5-95;
- probabilidad empírica de ocupar top 1, top 5 y top 10.

Estas probabilidades son **condicionales a esta familia de pesos y a los datos disponibles**. No son probabilidades de éxito de una intervención ni una inferencia estadística sobre la población.

## 7. Diagnóstico espacial

Se construye una matriz binaria k-nearest-neighbours sobre centroides de barrio, con `k=5` y normalización por fila. Se calcula Moran global:

```text
I = (n / S0) * sum_i sum_j w_ij (x_i - x_bar)(x_j - x_bar) / sum_i (x_i - x_bar)^2
```

La significación global se aproxima mediante 999 permutaciones bilaterales con semilla 42. También se publican cuadrantes descriptivos basados en el score estandarizado y su lag espacial: `high-high`, `high-low`, `low-high` y `low-low`. No se calcula ni afirma significación local para esos cuadrantes.

## 8. Plan contrafactual de áreas de revisión

El candidato inicial es cualquier punto de la malla de 150 m que se encuentra por encima de 250 m de distancia. Se seleccionan como máximo 25 áreas con:

- separación mínima de 350 m entre áreas seleccionadas;
- máximo de tres áreas por barrio;
- objetivo greedy de reducción de déficit de distancia ponderado.

En cada paso, para cada candidato `j` se calcula la ganancia:

```text
G_j = sum_i [max(d_i - 250, 0) - max(min(d_i, d_ij) - 250, 0)] * q_i
q_i = 1 + 1,5 * prioridad_i + 0,75 * P_i(top 10)
```

`d_i` es la distancia actual del punto de malla `i` al aparcamiento más cercano y `d_ij` su distancia al candidato `j`. La ponderación `q_i` da mayor importancia a déficit de distancia en barrios prioritarios y robustos. El resultado expresa una ganancia de distancia ponderada, no número de usuarios, demanda o retorno económico.

Las coordenadas generadas son puntos de cribado. Antes de cualquier propuesta real deben comprobarse calle, propiedad, obstáculos, red ciclista, seguridad, demanda, capacidad y condiciones urbanísticas.

## 9. Reproducibilidad

```bash
python -m pip install -r requirements-dev.txt
python -m ruff check .
python -m pytest
python src/run_pipeline.py
streamlit run app.py
```

El pipeline usa los snapshots versionados por defecto. `python src/fetch_data.py` actualiza fuentes antes de una nueva ejecución y cambia el manifiesto de trazabilidad.

## 10. Limitaciones

- La malla es una aproximación espacial y no sustituye análisis de red.
- Las plazas declaradas no informan de ocupación, mantenimiento o accesibilidad universal.
- El área del barrio no sustituye población, empleo, visitantes o uso del suelo.
- Los resultados dependen de indicadores y pesos elegidos.
- La simulación no modela capacidad de los nuevos aparcamientos, coste ni desplazamiento de demanda.
