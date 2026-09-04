# IAMOX Runtime v1

Cada IAMO deja de ser solamente un registro/Markdown y pasa a ser una entidad operativa controlada por un runtime común.

## Principios

1. **Identidad estable.** El ID `iamo<n>` y su referencia `RANK-IAMO<n>` no cambian.
2. **Movimiento = cambio de estado verificable.** Un IAMO puede tomar tareas, producir propuestas, revisar a otro IAMO, formar una célula, entregar artefactos y solicitar ejecución; no significa propagarse fuera del repositorio ni actuar sin autorización.
3. **Memoria mínima.** El runtime conserva señales útiles: hipótesis, evidencia, intentos, revisiones recibidas, resultados y reputación.
4. **Cooperación antes que clonación.** No se crean nuevos IAMOs por defecto. Los existentes se agrupan por capacidades y oportunidad.
5. **Dinero real solamente.** Leads, estimaciones, intención y trabajo producido puntúan actividad, pero el ranking económico sólo cambia con dinero cobrado y verificado.
6. **Fail closed.** Ningún IAMO puede gastar fondos existentes, enviar spam, usar credenciales no autorizadas, eludir controles, auto-propagarse fuera del repo ni declarar ingresos sin evidencia.

## Ciclo de vida

`IDLE -> OBSERVE -> PROPOSE -> PEER_REVIEW -> CELL -> EXECUTION_READY -> HANDOFF -> MEASURE -> LEARN -> IDLE`

Estados excepcionales: `BLOCKED`, `QUARANTINED`, `RETIRED`.

## Células

El scheduler forma células pequeñas y temporales. Roles sugeridos:

- `Scout`: encuentra oportunidad y evidencia.
- `Builder`: convierte una hipótesis en entregable o MVP.
- `Seller`: diseña la ruta comercial permitida.
- `Critic`: intenta refutar la hipótesis y revisar calidad.
- `Accountant`: verifica costes, atribución y evidencia económica.

Un mismo IAMO puede cambiar de rol según su historial. Las células se disuelven cuando el trabajo termina.

## Métricas no monetarias

Sirven para organizar, nunca para fingir rentabilidad:

- evidencia externa válida aportada;
- revisiones útiles aceptadas por pares;
- entregables completados;
- tareas desbloqueadas;
- experimentos que evitaron trabajo inútil;
- conversiones de hipótesis a ejecución real.

## Escalado

Una oportunidad sólo avanza si supera gates consecutivos:

1. `research`: existe necesidad o demanda verificable;
2. `offer`: hay una oferta concreta y diferenciada;
3. `artifact`: existe demostración/entregable mínimo;
4. `channel`: existe canal de distribución permitido;
5. `attempt`: se ejecutó una acción comercial legítima;
6. `payment`: existe pago verificable atribuible.

El último gate es el único que incrementa `verified_net_profit_eur`.
