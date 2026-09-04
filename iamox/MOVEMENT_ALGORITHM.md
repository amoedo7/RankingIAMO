# Algoritmo de movimiento IAMOX

El movimiento no es “ejecutar cosas al azar”; es cambiar de posición dentro de una red de trabajo verificable.

## Ronda

Para cada heartbeat:

1. `scan_population()` — materializa un estado operativo por IAMO histórico.
2. `score_capacity()` — usa reputación + rasgos para saber dónde aporta más cada IAMO.
3. `scan_opportunities()` — lee oportunidades ya registradas y las convierte en tareas.
4. `form_cells()` — elige perfiles complementarios sin repetir agentes dentro de la misma ronda.
5. `peer_review()` — un crítico intenta refutar antes de escalar.
6. `route_gate()` — sólo mueve la oportunidad si cumple evidencia del gate actual.
7. `handoff_execution()` — acciones externas salen por un owner permitido.
8. `measure_outcome()` — captura evidencia, resultado y coste.
9. `learn()` — actualiza reputación/memoria.
10. `release_cell()` — devuelve IAMOs al pool.

## Función de prioridad

Una célula no se selecciona por “qué IAMO habla más”, sino por capacidad combinada:

`priority = evidence*3 + delivery*3 + peer_help*2 + economic_truth*5 + execution + coordination`

La verdad económica pesa más que volumen de actividad.

## Replicación

El runtime común se aplica a todos los IAMOs existentes. No se clona código por cada IAMO: una sola implementación gobierna miles de estados. Así una mejora del algoritmo beneficia a toda la población en el siguiente heartbeat.

## Evolución mutua

Una lección sólo se difunde si se puede vincular a evidencia o a un resultado real. El runtime puede promoverla a `accepted_lessons`; los patrones que fracasan se guardan en `failed_patterns` para reducir repetición.

## Límites

- máximo 21 células activas por defecto;
- cada IAMO pertenece como máximo a una célula por ronda;
- ninguna célula puede certificar su propio ingreso;
- sin evidencia externa, una tarea queda en `peer_review`/`research`;
- no hay nuevos IAMOs automáticos mientras la población existente no esté siendo aprovechada.
