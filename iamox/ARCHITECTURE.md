# Arquitectura IAMOX vivos

## Qué significa "movilidad"

Un IAMO ya no queda congelado en su archivo histórico. Su identidad se proyecta a `iamox/state/agents.json` y el scheduler puede cambiar su estado, asignarlo a una célula, vincularlo a una tarea, registrar revisiones y devolverlo al pool.

El archivo histórico sigue siendo evidencia. El estado operativo es mutable y auditable.

## Algoritmo común

Cada heartbeat ejecuta:

1. **Bootstrap**: lee todos los competidores existentes y garantiza un agente operativo por identidad.
2. **Specialize**: asigna un rol inicial determinista y rasgos reproducibles; el historial puede modificar reputación después.
3. **Queue**: transforma oportunidades existentes en tareas, sin fabricar demanda ni ingresos.
4. **Match**: forma células temporales con perfiles complementarios.
5. **Peer review**: ninguna hipótesis escala por autoaprobación; otra función debe intentar refutarla.
6. **Gate**: research -> offer -> artifact -> channel -> attempt -> payment.
7. **Handoff**: las acciones externas permitidas pasan a EjecutorIAMO u otro owner explícito; el IAMO no adquiere permisos por sí mismo.
8. **Measure**: outcomes y evidencia vuelven a memoria/reputación.
9. **Recycle**: la célula se disuelve y sus IAMOs vuelven disponibles.

## Organización Fibonacci

El runtime puede observar cientos de IAMOs pero limita el trabajo simultáneo. Por defecto forma como máximo **21 células** en una ronda. Las oportunidades deben ir reduciéndose por evidencia, no creciendo por generación automática:

`muchos intentos -> 21 células -> 13 oportunidades -> 8 con evidencia -> 5 ofertas -> 3 ejecuciones -> 2 compradores/interés verificable -> 1 pago`

Los números son límites de capacidad y priorización, no una afirmación matemática de éxito.

## Mejorarse mutuamente

La mejora colectiva usa cuatro señales:

- `peer_reviews`: una célula recibe crítica de un IAMO que no originó la hipótesis;
- `accepted_lessons`: aprendizajes que sobrevivieron a evidencia;
- `failed_patterns`: patrones que otro IAMO debe evitar repetir;
- `reputation`: evidencia, ayuda a pares, entrega y verdad económica.

Nunca se recompensa escribir más texto. Se recompensa reducir incertidumbre y producir evidencia/entregables verificables.

## Seguridad económica

`iamox/runtime.py` no tiene permiso para escribir dinero verificado. El campo de tareas permanece `0.00`; el ledger económico canónico sigue siendo `data/earnings.jsonl` y su verificador.

Esto evita que una población de agentes pueda autocertificarse ganancias.
