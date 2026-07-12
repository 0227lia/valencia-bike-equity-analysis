# Resumen ejecutivo

Este proyecto realiza un cribado geoespacial reproducible para identificar barrios y zonas de Valencia que merecen una revisión más detallada de aparcamiento de bicicletas. Combina vulnerabilidad urbana, capacidad declarada y distancia al aparcamiento más cercano.

## Qué aporta el análisis

- **70 barrios** y **4.316 puntos de aparcamiento** procesados desde snapshots públicos.
- Malla de diagnóstico de 300 m y malla de simulación de 150 m.
- **10.000 simulaciones de pesos**: 9 barrios tienen al menos un 80% de probabilidad de mantenerse en el top 10.
- Moran global I=0.255; prueba por permutación bilateral p=0.001 con k=5.
- En el escenario de 25 áreas de revisión, el modelo reduce el déficit de distancia ponderado un 71.0% y lleva 179 puntos de malla por debajo del umbral.

## Ranking con incertidumbre

- **El Grau** (Poblats Marítims): rango base 1, rango esperado 1.0, intervalo 5-95 1-1, P(top 10)=100.0%.
- **La Punta** (Quatre Carreres): rango base 2, rango esperado 2.2, intervalo 5-95 2-3, P(top 10)=99.9%.
- **El Calvari** (Campanar): rango base 3, rango esperado 4.3, intervalo 5-95 2-11, P(top 10)=93.8%.
- **En Corts** (Quatre Carreres): rango base 4, rango esperado 4.7, intervalo 5-95 4-7, P(top 10)=99.3%.
- **Ciutat Fallera** (Benicalap): rango base 5, rango esperado 5.2, intervalo 5-95 3-6, P(top 10)=100.0%.
- **Soternes** (L'Olivereta): rango base 6, rango esperado 6.8, intervalo 5-95 5-10, P(top 10)=95.0%.
- **Cami De Vera** (Benimaclet): rango base 7, rango esperado 7.7, intervalo 5-95 3-19, P(top 10)=81.5%.
- **Sant Marcel.Li** (Jesus): rango base 8, rango esperado 7.8, intervalo 5-95 7-9, P(top 10)=97.4%.
- **La Creu Coberta** (Jesus): rango base 9, rango esperado 9.5, intervalo 5-95 6-13, P(top 10)=82.7%.
- **La Fonteta S.Lluis** (Quatre Carreres): rango base 10, rango esperado 10.2, intervalo 5-95 8-13, P(top 10)=63.1%.

## Sensibilidad a políticas explícitas

- `default`: correlación de rangos=1.000; solapamiento top 10=10/10.
- `equity_focus`: correlación de rangos=0.949; solapamiento top 10=8/10.
- `access_focus`: correlación de rangos=0.917; solapamiento top 10=5/10.

## Áreas de revisión modeladas

- Puesto 1: **El Grau** (Poblats Marítims), distancia actual=1470 m, ganancia marginal ponderada=190557 m.
- Puesto 2: **El Grau** (Poblats Marítims), distancia actual=1861 m, ganancia marginal ponderada=129274 m.
- Puesto 3: **La Punta** (Quatre Carreres), distancia actual=1044 m, ganancia marginal ponderada=73545 m.
- Puesto 4: **La Punta** (Quatre Carreres), distancia actual=1104 m, ganancia marginal ponderada=60301 m.
- Puesto 5: **El Grau** (Poblats Marítims), distancia actual=1198 m, ganancia marginal ponderada=36288 m.
- Puesto 6: **La Punta** (Quatre Carreres), distancia actual=742 m, ganancia marginal ponderada=22004 m.
- Puesto 7: **Sant Pau** (Campanar), distancia actual=731 m, ganancia marginal ponderada=18834 m.
- Puesto 8: **Natzaret** (Poblats Marítims), distancia actual=259 m, ganancia marginal ponderada=11460 m.
- Puesto 9: **Malilla** (Quatre Carreres), distancia actual=630 m, ganancia marginal ponderada=11353 m.
- Puesto 10: **Natzaret** (Poblats Marítims), distancia actual=616 m, ganancia marginal ponderada=10162 m.

## Interpretación y límites

Las áreas de revisión no son propuestas de obra. El modelo usa distancia en línea recta, no rutas reales, demanda, ocupación, capacidad futura, coste, propiedad, red viaria ni restricciones urbanísticas. Moran es un diagnóstico global exploratorio; los cuadrantes locales no son pruebas de significación. Cualquier intervención requeriría validación de calle, participación, datos de demanda y una evaluación técnica municipal.
