# Resumen ejecutivo

Este análisis prioriza barrios de Valencia para ampliar la red de aparcamientos de bicicleta. El criterio combina vulnerabilidad urbana, capacidad existente y distancia estimada hasta el aparcamiento más cercano.

## Métricas principales

- Barrios analizados: 70
- Ubicaciones candidatas propuestas: 24
- Barrio con mayor prioridad: EL GRAU (POBLATS MARÍTIMS)
- Mediana de distancia p90 al aparcamiento más cercano: 85 metros

## Barrios con mayor prioridad

- EL GRAU (POBLATS MARÍTIMS): prioridad=0.846, plazas/km2=90.7, cobertura insuficiente=78.9%
- LA PUNTA (QUATRE CARRERES): prioridad=0.711, plazas/km2=8.4, cobertura insuficiente=80.6%
- EL CALVARI (CAMPANAR): prioridad=0.614, plazas/km2=640.5, cobertura insuficiente=0.0%
- EN CORTS (QUATRE CARRERES): prioridad=0.599, plazas/km2=351.6, cobertura insuficiente=0.0%
- CIUTAT FALLERA (BENICALAP): prioridad=0.596, plazas/km2=281.7, cobertura insuficiente=0.0%
- SOTERNES (L'OLIVERETA): prioridad=0.589, plazas/km2=401.2, cobertura insuficiente=0.0%
- CAMI DE VERA (BENIMACLET): prioridad=0.583, plazas/km2=176.5, cobertura insuficiente=37.5%
- SANT MARCEL.LI (JESUS): prioridad=0.577, plazas/km2=236.1, cobertura insuficiente=0.0%
- LA CREU COBERTA (JESUS): prioridad=0.564, plazas/km2=106.7, cobertura insuficiente=0.0%
- LA FONTETA S.LLUIS (QUATRE CARRERES): prioridad=0.561, plazas/km2=175.9, cobertura insuficiente=0.0%

## Sensibilidad del ranking

Se comparó el escenario base con alternativas que dan más peso a equidad o accesibilidad.
La correlación mide estabilidad global y el solapamiento indica cuántos barrios permanecen en el top 10.

- default: correlación=1.000, coincidencia top 10=10/10
- equity_focus: correlación=0.949, coincidencia top 10=8/10
- access_focus: correlación=0.917, coincidencia top 10=5/10

## Ubicaciones candidatas principales

- Puesto 1: EL GRAU (POBLATS MARÍTIMS), lat=39.432217, lon=-0.311742, aparcamiento existente más cercano=2241m
- Puesto 2: EL GRAU (POBLATS MARÍTIMS), lat=39.448386, lon=-0.304762, aparcamiento existente más cercano=2114m
- Puesto 3: EL GRAU (POBLATS MARÍTIMS), lat=39.426827, lon=-0.311742, aparcamiento existente más cercano=2006m
- Puesto 4: LA PUNTA (QUATRE CARRERES), lat=39.433079, lon=-0.347491, aparcamiento existente más cercano=1119m
- Puesto 5: LA PUNTA (QUATRE CARRERES), lat=39.433079, lon=-0.337022, aparcamiento existente más cercano=1034m
- Puesto 6: LA PUNTA (QUATRE CARRERES), lat=39.438469, lon=-0.354470, aparcamiento existente más cercano=1028m
- Puesto 7: CAMI DE VERA (BENIMACLET), lat=39.488291, lon=-0.348039, aparcamiento existente más cercano=581m
- Puesto 8: NATZARET (POBLATS MARÍTIMS), lat=39.438992, lon=-0.334886, aparcamiento existente más cercano=524m
- Puesto 9: CAMI REAL (JESUS), lat=39.446623, lon=-0.404109, aparcamiento existente más cercano=479m
- Puesto 10: SANT PAU (CAMPANAR), lat=39.485638, lon=-0.421314, aparcamiento existente más cercano=984m

## Interpretación

El score de prioridad debe leerse como una señal de apoyo al análisis, no como una decisión automática. El siguiente paso sería validar las ubicaciones candidatas con información de calle, demanda ciclista, disponibilidad de espacio y restricciones urbanísticas.