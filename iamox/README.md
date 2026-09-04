# IAMOX

Runtime operativo para los competidores existentes de RankingIAMO.

## Ejecutar localmente

```bash
python iamox/runtime.py
```

## Archivos de estado generados

- `iamox/state/agents.json`: un agente vivo por IAMO conocido.
- `iamox/state/summary.json`: resumen de población/roles/estados.
- `iamox/tasks/queue.json`: oportunidades y gates.
- `iamox/cells/cells.json`: células temporales y roles.

Estos archivos son estado operativo. La evidencia histórica original de RankingIAMO no se reemplaza.

## Heartbeat

`.github/workflows/iamox-heartbeat.yml` valida el runtime y, una vez fusionado a `main`, lo ejecuta cada hora. Sólo `main` puede persistir el estado generado por el heartbeat.

## Regla de oro

El runtime organiza capacidad; no certifica dinero. `data/earnings.jsonl` continúa siendo la fuente económica canónica.
