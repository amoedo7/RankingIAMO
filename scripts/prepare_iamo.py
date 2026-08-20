#!/usr/bin/env python3

import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RUNTIME = ROOT / "runtime"
COMPETITORS = DATA / "competitors.json"
ATTEMPTS = DATA / "attempts.jsonl"
LEADERBOARD = ROOT / "leaderboard.json"
BASE_PROMPT = ROOT / "PROMPT_COMPETIDOR.md"
COBRAMO_URL = "https://cobramo.netlify.app/"


def now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def load_attempts(limit=80):
    if not ATTEMPTS.exists():
        return []
    rows = []
    for raw in ATTEMPTS.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        try:
            rows.append(json.loads(raw))
        except json.JSONDecodeError:
            continue
    return rows[-limit:]


def next_number(competitors):
    numbers = []
    for item in competitors:
        try:
            numbers.append(int(item.get("number", 0)))
        except (TypeError, ValueError):
            pass
    return max(numbers, default=0) + 1


def compact_history(rows):
    compact = []
    for row in rows:
        result = row.get("result") or {}
        compact.append(
            {
                "name": row.get("competitor_name"),
                "opportunity": result.get("opportunity"),
                "target_customer": result.get("target_customer"),
                "offer": result.get("offer"),
                "price": result.get("price"),
                "currency": result.get("currency"),
                "differentiation": result.get("differentiation_from_previous"),
                "verified_net_profit_eur": row.get("verified_net_profit_eur", "0.00"),
                "status": row.get("status"),
            }
        )
    return compact


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    RUNTIME.mkdir(parents=True, exist_ok=True)

    state = load_json(COMPETITORS, {"schema_version": "1.0", "competitors": []})
    competitors = state.setdefault("competitors", [])
    number = next_number(competitors)
    name = f"IAMO{number}"
    born_at = now_iso()

    identity = {
        "id": name.lower(),
        "name": name,
        "number": number,
        "born_at": born_at,
        "workflow_run_id": os.environ.get("GITHUB_RUN_ID"),
        "workflow_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        "repository": os.environ.get("GITHUB_REPOSITORY", "amoedo7/RankingIAMO"),
        "score_eur": "0.00",
    }
    (RUNTIME / "identity.json").write_text(
        json.dumps(identity, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    history = compact_history(load_attempts())
    leaderboard = load_json(LEADERBOARD, {"entries": []})
    base_prompt = BASE_PROMPT.read_text(encoding="utf-8")

    context = {
        "your_identity": identity,
        "cobramo": COBRAMO_URL,
        "current_leaderboard": leaderboard.get("entries", [])[:20],
        "recent_competitor_attempts": history,
    }

    instructions = f"""

# RONDA AUTONOMA ACTUAL

Tu identidad en ESTA ejecución es **{name}**. Sos un competidor nuevo e individual. No sos IAMO anteriores y no heredes sus afirmaciones como hechos.

Antes de elegir una idea:

1. Leé el contexto del repositorio y el historial de intentos anteriores.
2. Usá búsqueda web para investigar oportunidades reales y actuales.
3. Inspeccioná {COBRAMO_URL} para conocer las formas públicas disponibles para que un cliente pague a AMO.
4. Evitá repetir exactamente una estrategia anterior salvo que puedas explicar una mejora concreta.
5. Priorizá una acción que pueda producir una venta real con coste inicial cero o muy bajo.

Tus herramientas en esta ejecución son deliberadamente de SOLO LECTURA sobre el repositorio y la web. No afirmes que enviaste emails, publicaste mensajes, cobraste, desplegaste, llamaste a alguien o ejecutaste una acción externa si la herramienta no te permitió realmente hacerlo.

Tu trabajo debe producir un **paquete de ejecución** suficientemente concreto para que un ejecutor autorizado pueda materializarlo sin volver a inventar la estrategia: cliente objetivo, oferta, precio, canal, texto listo para usar, entregable o demo propuesta, URLs de investigación y el enlace de CobrAMO.

El ranking financiero es soberano: esta respuesta NO puede adjudicarte dinero. Aunque encuentres una oportunidad excelente, `revenue_claim_eur` debe ser `"0.00"`. Solo `data/earnings.jsonl` con verificación externa puede darte puntos después.

Respondé exclusivamente con UN objeto JSON válido, sin Markdown, sin bloques de código y sin texto antes o después. Debe tener exactamente esta estructura lógica:

{{
  "competitor_name": "{name}",
  "summary": "resumen corto de la jugada",
  "opportunity": "problema real detectado",
  "target_customer": "cliente específico",
  "offer": "qué se vendería",
  "price": "precio propuesto como texto",
  "currency": "EUR u otra moneda",
  "why_now": "evidencia de oportunidad actual",
  "research_urls": ["https://..."],
  "actions_completed": ["investigaciones o artefactos realmente realizados en esta ejecución"],
  "execution_packet": {{
    "channel": "canal autorizado recomendado",
    "subject": "asunto si aplica",
    "message": "mensaje final listo para usar, sin spam masivo",
    "deliverable": "qué debe entregarse al cliente",
    "cobramo_url": "{COBRAMO_URL}"
  }},
  "expected_revenue_eur": "estimación, no ingreso real",
  "direct_cost_eur": "0.00 salvo coste inevitable conocido",
  "confidence_0_100": 0,
  "differentiation_from_previous": "qué aprendiste o cambiaste respecto a IAMOs anteriores",
  "next_step": "acción externa concreta de mayor valor",
  "revenue_claim_eur": "0.00",
  "notes": "riesgos, supuestos o aprendizaje"
}}
"""

    full_prompt = (
        base_prompt
        + instructions
        + "\n\n# CONTEXTO MACHINE-READABLE\n"
        + json.dumps(context, ensure_ascii=False, indent=2)
    )
    (RUNTIME / "prompt.txt").write_text(full_prompt, encoding="utf-8")

    output_path = os.environ.get("GITHUB_OUTPUT")
    if output_path:
        with open(output_path, "a", encoding="utf-8") as fh:
            fh.write(f"iamo_name={name}\n")
            fh.write(f"iamo_number={number}\n")

    print(name)


if __name__ == "__main__":
    main()
