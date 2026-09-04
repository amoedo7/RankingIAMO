# Esquema de estado IAMOX

Cada agente materializado en `iamox/state/agents.json` usa como mínimo:

```json
{
  "id": "iamo7",
  "name": "IAMO7",
  "number": 7,
  "payment_reference": "RANK-IAMO7",
  "role": "scout",
  "state": "idle",
  "cell_id": null,
  "task_id": null,
  "heartbeat_at": "2026-09-04T00:00:00Z",
  "reputation": {
    "evidence": 0,
    "peer_help": 0,
    "delivery": 0,
    "economic_truth": 0
  },
  "memory": {
    "accepted_lessons": [],
    "failed_patterns": [],
    "successful_patterns": []
  },
  "traits": {
    "exploration": 0.0,
    "execution": 0.0,
    "skepticism": 0.0,
    "commercial": 0.0,
    "coordination": 0.0
  }
}
```

Los `traits` iniciales son deterministas por ID para distribuir diversidad sin gastar una inferencia de IA en 983 perfiles. La reputación y la memoria son las partes que deben evolucionar con evidencia real.
