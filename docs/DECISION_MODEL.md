# Tarjeta de decisión

## Resumen

`Valencia Bike Equity` es un sistema analítico exploratorio que prioriza barrios y zonas de revisión para evaluar la red de aparcamiento de bicicletas. No automatiza decisiones públicas ni recomienda inversiones concretas.

## Uso previsto

- Preparar una revisión territorial inicial con datos abiertos.
- Identificar qué señales explican la prioridad de un barrio.
- Comparar políticas de ponderación de forma transparente.
- Preparar una lista corta de zonas que requieren inspección técnica de calle.

## Usos no previstos

- Determinar dónde se construirá infraestructura.
- Inferir demanda, seguridad, coste, impacto causal o rentabilidad.
- Valorar individuos, hogares, empresas o colectivos concretos.
- Sustituir trabajo de campo, participación o evaluación municipal.

## Entradas y salidas

| Elemento | Descripción |
|---|---|
| Entradas | Aparcamientos públicos, geometrías de barrio e indicadores agregados de vulnerabilidad. |
| Modelo | MCDA lineal, escenarios de pesos, simulación Dirichlet, Moran global y selección greedy. |
| Salidas | Ranking de barrios, intervalos de rango, cuadrantes descriptivos, áreas de revisión y frontera de impacto. |

## Evidencia de calidad

- Datos raw versionados con SHA-256 y pipeline reproducible sin red.
- Tests unitarios para geometrías, score, robustez, espacialidad y planificación.
- Ruff y pytest en CI; la acción reconstruye las salidas desde el snapshot incluido.
- Semilla fija (`42`) para resultados estables en las simulaciones y permutaciones.

## Riesgos y controles

| Riesgo | Control implementado | Riesgo residual |
|---|---|---|
| Pesos subjetivos | Escenarios explícitos y 10.000 muestras Dirichlet. | Los pesos no representan consenso social. |
| Resolución espacial | Malla de simulación más fina (150 m). | La distancia sigue siendo una aproximación. |
| Interpretación excesiva | Etiqueta `modeled_review_area` y límites visibles en informes. | Un mapa puede parecer más preciso de lo que es. |
| Agrupación espacial | Moran global por permutación y cuadrantes descriptivos. | No se estima significación local. |
| Obsolescencia de datos | Manifiesto, snapshots y comando de actualización. | La red física puede cambiar entre descargas. |

## Revisión recomendada antes de uso externo

1. Actualizar las fuentes y revisar el manifiesto.
2. Inspeccionar cambios en el ranking y la robustez.
3. Validar las áreas de revisión sobre calle y red ciclista.
4. Incorporar demanda, ocupación, accesibilidad universal, coste y restricciones urbanísticas.
5. Documentar la política de pesos acordada con las partes implicadas.
