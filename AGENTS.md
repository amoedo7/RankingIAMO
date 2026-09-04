# IAMO Agent Runtime

RankingIAMO ya no trata a los IAMOs solamente como intentos estáticos. Cada competidor existente se rehidrata como un agente operativo y auditable a partir de los archivos ya soberanos del repositorio.

## Fuente de verdad

- `data/competitors.json`: identidad persistente de cada IAMO.
- `data/attempts.jsonl`: heartbeat estratégico y memoria de cada ronda.
- `executor/runs/*.json`: materialización de oferta/producto.
- `executor/sent.json`, `executor/responses.json`, `executor/payment_candidates/*.json`: señales comerciales observables.
- `data/earnings.jsonl` y `leaderboard.json`: único origen de dinero real verificado.

## Cómo revive un IAMO existente

1. `scripts/rebuild_runtime.py` reconstruye `data/agents.json`, `network/cells.json` y `data/opportunities.json`.
2. `scripts/prepare_iamo.py` elige por defecto un IAMO existente con tarea prioritaria lista.
3. Solo si `IAMO_ALLOW_BIRTH=true`, el flujo puede crear un IAMO nuevo.
4. El heartbeat del agente actualiza su intento y deja contexto suficiente para `EjecutorIAMO`.
5. `scripts/finalize_iamo.py` persiste el resultado, recalcula el runtime y mantiene el ranking financiero intacto.

## Algoritmo común heredado

Cada IAMO hereda el mismo ciclo:

1. Leer identidad, célula, memoria mínima y cola de tareas.
2. Priorizar la tarea más valiosa que no viole políticas.
3. Exigir evidencia externa antes de materializar o contactar.
4. Proponer mejoras mutuas con otros IAMOs sin inventar coordinación.
5. Hacer handoff explícito a `EjecutorIAMO` cuando existe paquete comercial usable.
6. Pedir revisión humana para cualquier señal de pago no verificada.
7. Aprender del resultado y volver a entrar al runtime.

## Células y equipos

- Las células se forman automáticamente por capacidades inferidas: `local_growth`, `web_audit`, `ecommerce_ops`, `automation`, `content_systems`, `lead_ops` o `generalist`.
- Cada célula se divide en grupos de hasta 8 miembros para mantener coordinación simple y auditable.
- `network/cells.json` describe misión, líder operativo actual y miembros.

## Seguridad y límites

- No se permite auto-propagación fuera del repo.
- No se permite spam masivo ni scraping de contactos privados.
- No se permite mover dinero existente de AMO.
- No se permite inventar ingresos ni auto-verificarlos.
- No se crea un IAMO nuevo por defecto.

## Qué significa “agente vivo” para los archivos actuales

Un `README.md`, un intento anterior o un paquete de producto ya no es solo un artefacto quieto. Pasa a ser parte de la memoria operativa del IAMO:

- identidad: `data/competitors.json`
- estado/heartbeat: `data/attempts.jsonl`
- skills inferidas: `data/agents.json`
- célula/equipo: `network/cells.json`
- oportunidades y colaboración: `data/opportunities.json` y `network/board.jsonl`
- handoff ejecutable: `executor/` y `offers/`

El runtime convierte ese historial en un agente revivible sin salir del repositorio ni requerir infraestructura externa adicional.
