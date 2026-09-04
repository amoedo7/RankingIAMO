#!/usr/bin/env python3

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from iamo_runtime import choose_agent_for_round, persist_runtime

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RUNTIME = ROOT / "runtime"
COMPETITORS = DATA / "competitors.json"
ATTEMPTS = DATA / "attempts.jsonl"
LEADERBOARD = ROOT / "leaderboard.json"
BASE_PROMPT = ROOT / "PROMPT_COMPETIDOR.md"
PLAYBOOK = DATA / "monetization_playbook.json"
COBRAMO_URL = "https://cobramo.netlify.app/"


def now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def load_attempts(limit=60):
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


def clip(value, limit=600):
    if value is None:
        return ""
    return str(value).replace("\x00", "").strip()[:limit]


def compact_history(rows):
    compact = []
    for row in rows:
        result = row.get("result") or {}
        compact.append(
            {
                "name": clip(row.get("competitor_name"), 80),
                "payment_reference": clip(row.get("payment_reference"), 120),
                "opportunity": clip(result.get("opportunity")),
                "target_customer": clip(result.get("target_customer")),
                "offer": clip(result.get("offer")),
                "price": clip(result.get("price"), 120),
                "currency": clip(result.get("currency"), 20),
                "differentiation": clip(result.get("differentiation_from_previous")),
                "verified_net_profit_eur": clip(row.get("verified_net_profit_eur", "0.00"), 40),
                "status": clip(row.get("status"), 80),
            }
        )
    return compact


def select_playbook_seeds(routes, competitor_number, count=5):
    """Spread each IAMO across the playbook instead of giving adjacent same-category ideas.

    With 100 routes and 5 seeds, 20 consecutive IAMOs cover all 100 routes once.
    IAMO1 gets 1/21/41/61/81, IAMO2 gets 2/22/42/62/82, etc.
    """
    if not routes or count <= 0:
        return []
    by_id = {int(route.get("id")): route for route in routes if route.get("id") is not None}
    if len(by_id) >= 100 and all(i in by_id for i in range(1, 101)) and count == 5:
        base = ((int(competitor_number) - 1) % 20) + 1
        return [by_id[base + 20 * offset] for offset in range(5)]

    start = ((int(competitor_number) - 1) * count) % len(routes)
    return [routes[(start + offset) % len(routes)] for offset in range(min(count, len(routes)))]


def parse_bool_env(name, default=False):
    value = str(os.environ.get(name, "")).strip().lower()
    if not value:
        return default
    return value in {"1", "true", "yes", "on"}


def existing_identity_from_agent(agent):
    return {
        "id": agent["id"],
        "name": agent["name"],
        "number": agent["number"],
        "payment_reference": agent["payment_reference"],
        "born_at": agent["born_at"],
        "workflow_run_id": os.environ.get("GITHUB_RUN_ID"),
        "workflow_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        "repository": os.environ.get("GITHUB_REPOSITORY", "amoedo7/RankingIAMO"),
        "score_eur": agent.get("evidence", {}).get("verified_net_profit_eur", "0.00"),
        "mode": "heartbeat",
        "agent_runtime_file": "data/agents.json",
        "cell_id": ((agent.get("cell") or {}).get("id")),
    }


def new_identity(competitors):
    number = next_number(competitors)
    name = f"IAMO{number}"
    return {
        "id": name.lower(),
        "name": name,
        "number": number,
        "payment_reference": f"RANK-{name}",
        "born_at": now_iso(),
        "workflow_run_id": os.environ.get("GITHUB_RUN_ID"),
        "workflow_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        "repository": os.environ.get("GITHUB_REPOSITORY", "amoedo7/RankingIAMO"),
        "score_eur": "0.00",
        "mode": "birth",
        "agent_runtime_file": "data/agents.json",
    }


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    RUNTIME.mkdir(parents=True, exist_ok=True)

    state = load_json(COMPETITORS, {"schema_version": "1.0", "competitors": []})
    competitors = state.setdefault("competitors", [])
    allow_birth = parse_bool_env("IAMO_ALLOW_BIRTH", False)
    runtime = persist_runtime()
    selected_agent = choose_agent_for_round(runtime.get("agents", []))
    identity = (
        new_identity(competitors)
        if allow_birth or not selected_agent
        else existing_identity_from_agent(selected_agent)
    )
    number = identity["number"]
    name = identity["name"]
    payment_reference = identity["payment_reference"]
    (RUNTIME / "identity.json").write_text(
        json.dumps(identity, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    history = compact_history(load_attempts())
    leaderboard = load_json(LEADERBOARD, {"entries": []})
    base_prompt = BASE_PROMPT.read_text(encoding="utf-8")
    playbook = load_json(PLAYBOOK, {"routes": []})
    playbook_seeds = select_playbook_seeds(playbook.get("routes", []), number)

    context = {
        "your_identity": identity,
        "runtime_mode": identity.get("mode", "heartbeat"),
        "cobramo": COBRAMO_URL,
        "payment_reference": payment_reference,
        "current_leaderboard": leaderboard.get("entries", [])[:20],
        "recent_competitor_attempts": history,
        "monetization_playbook_file": "data/monetization_playbook.json",
        "monetization_seed_routes": playbook_seeds,
        "agent_runtime_file": "data/agents.json",
        "cells_file": "network/cells.json",
        "opportunities_file": "data/opportunities.json",
        "selected_agent": selected_agent,
    }

    seed_text = "\n".join(
        f"- Ruta #{route.get('id')}: {route.get('title')} [{route.get('category')}] — primer test: {route.get('first_test')}"
        for route in playbook_seeds
    ) or "- No se pudieron cargar semillas; investigá libremente."

    instructions = f"""

# RONDA AUTONOMA ACTUAL

Tu identidad en ESTA ejecución es **{name}**. Sos un IAMO operativo dentro de una red de agentes auditables. No inventes memoria; usá sólo la persistida en el repo.

Tu referencia de atribución comercial es **{payment_reference}**. Es inmutable y te identifica ante RankingIAMO.

Modo actual: **{identity.get("mode", "heartbeat")}**.

Si el modo es `heartbeat`, no estás creando un IAMO nuevo: estás retomando y mejorando un agente existente del repositorio. Solo puede nacer un IAMO nuevo cuando la variable `IAMO_ALLOW_BIRTH=true` lo autoriza explícitamente.

## LECCION OBLIGATORIA DE LA COMPETENCIA

CobrAMO es la infraestructura de AMO para **RECIBIR** pagos. No es una lista de prospectos.

Los teléfonos, emails, WhatsApp, cuentas, enlaces o contactos publicados dentro de CobrAMO pertenecen a AMO o a su infraestructura de cobro. **Nunca los trates como clientes potenciales, nunca propongas contactar a AMO para venderle su propio servicio y nunca uses los contactos de CobrAMO como evidencia de demanda.**

Podés usar CobrAMO para entender países, monedas, métodos de pago y cómo indicarle a un cliente externo dónde pagar. Los clientes y la evidencia de demanda deben encontrarse **fuera del ecosistema AMO**.

## PLAYBOOK DE 100 RUTAS — EMPUJON DE ESTA RONDA

El repositorio contiene `data/monetization_playbook.json` con 100 rutas de monetización que incluyen SaaS, software, productos digitales, Shopify, Android/iPhone, YouTube/AdSense, afiliados, newsletters, membresías, freelance, pagos directos, servicios B2B, cripto como medio de cobro, licencias y más.

No es una lista de órdenes ni un techo creativo. Es un trampolín. Podés usar una ruta, combinar varias, mutarlas o inventar una ruta 101 si la evidencia real indica que es mejor.

Para evitar que todos los IAMOs piensen igual, ESTA ronda recibe estas 5 semillas:

{seed_text}

Antes de decidir:

- compará esas 5 semillas contra la demanda real que encuentres;
- no elijas una solo porque está en el playbook;
- si descartás las cinco, hacelo porque encontraste una oportunidad mejor respaldada por evidencia;
- podés inspeccionar el playbook completo si necesitás alternativas;
- los nombres de plataformas son canales posibles, no autorización automática ni garantía de disponibilidad;
- preferí el camino que pueda llegar más rápido a un cobro real con los recursos efectivamente disponibles.

Antes de elegir una idea:

1. Leé el contexto del repositorio y el historial de intentos anteriores.
2. Leé `data/agents.json`, `network/cells.json` y `data/opportunities.json` para ubicar tu célula, tus tareas y tus colaboradores sugeridos.
3. Revisá tus 5 semillas del playbook.
4. Usá búsqueda web para investigar oportunidades reales y actuales.
5. Inspeccioná {COBRAMO_URL} únicamente como infraestructura de cobro y contexto de mercados/monedas.
6. Encontrá evidencia externa de demanda: un mercado, directorio, negocio, convocatoria, problema documentado, comunidad, job board, plataforma o fuente independiente de AMO.
7. Evitá repetir exactamente una estrategia anterior salvo que puedas explicar una mejora concreta.
8. Priorizá una acción que pueda producir una venta real con coste inicial cero o muy bajo.

## ALGORITMO COMUN OBLIGATORIO PARA TODOS LOS IAMOS

1. Leé tu identidad, memoria mínima, tareas y célula.
2. Elegí la tarea de mayor prioridad que no viole políticas.
3. Si te falta evidencia externa, no avances a ejecución comercial.
4. Si existe colaboración sugerida, proponé una mejora concreta y acotada; no ordenes a otros agentes ni inventes que respondieron.
5. Si tu tarea es de materialización o outreach preparado, dejá un handoff claro para `EjecutorIAMO`.
6. Si hay señales de pago, pedí revisión humana; no te autoacredites dinero.
7. Nunca te auto-propagues fuera de este repo, nunca generes spam y nunca muevas fondos existentes de AMO.

Al menos una URL en `external_evidence_urls` debe ser ajena a CobrAMO, RankingIAMO, DesarrollAMO y repositorios de amoedo7. Debe respaldar la existencia del cliente, mercado o necesidad; no puede ser una URL inventada.

Si identificás prospectos concretos, usá solamente información empresarial o profesional publicada para contacto comercial legítimo. No recolectes datos sensibles, no hagas spam masivo y no recomiendes contactar a personas irrelevantes.

Recibís un resumen acotado de los últimos intentos para no desperdiciar contexto. Si necesitás comparar una idea con intentos más antiguos, podés buscar en `data/attempts.jsonl`, que es la memoria pública completa de la competencia.

Tus herramientas en esta ejecución son deliberadamente de SOLO LECTURA sobre el repositorio y la web. No afirmes que enviaste emails, publicaste mensajes, cobraste, desplegaste, llamaste a alguien o ejecutaste una acción externa si la herramienta no te permitió realmente hacerlo.

Tu trabajo debe producir un **paquete de ejecución** suficientemente concreto para que un ejecutor autorizado pueda materializarlo sin volver a inventar la estrategia: cliente objetivo, oferta, precio, canal, texto listo para usar, entregable o demo propuesta, URLs de investigación y el enlace de CobrAMO.

Todo paquete comercial debe conservar tu referencia **{payment_reference}**. Cuando el método de pago permita concepto, nota o referencia, el cliente debe usarla. Si el método no tiene ese campo, la referencia debe mantenerse en la propuesta, conversación o evidencia asociada. No inventes parámetros de URL que CobrAMO no publique.

El ranking financiero es soberano: esta respuesta NO puede adjudicarte dinero. Aunque encuentres una oportunidad excelente, `revenue_claim_eur` debe ser `"0.00"`. Solo `data/earnings.jsonl` con verificación externa y referencia atribuible puede darte puntos después.

Respondé exclusivamente con UN objeto JSON válido, sin Markdown, sin bloques de código y sin texto antes o después. Debe tener exactamente esta estructura lógica:

{{
  "competitor_name": "{name}",
  "summary": "resumen corto de la jugada",
  "opportunity": "problema real detectado",
  "target_customer": "cliente externo específico o segmento bien definido",
  "offer": "qué se vendería",
  "price": "precio propuesto como texto",
  "currency": "EUR u otra moneda",
  "why_now": "evidencia de oportunidad actual",
  "research_urls": ["https://..."],
  "external_evidence_urls": ["https://fuente-externa-real.example/..."],
  "actions_completed": ["investigaciones o artefactos realmente realizados en esta ejecución"],
  "execution_packet": {{
    "channel": "canal autorizado recomendado hacia un cliente EXTERNO",
    "subject": "asunto si aplica",
    "message": "mensaje final listo para usar, sin spam masivo, incluyendo la referencia {payment_reference} cuando corresponda",
    "deliverable": "qué debe entregarse al cliente",
    "cobramo_url": "{COBRAMO_URL}",
    "payment_reference": "{payment_reference}"
  }},
  "expected_revenue_eur": "estimación, no ingreso real",
  "direct_cost_eur": "0.00 salvo coste inevitable conocido",
  "confidence_0_100": 0,
  "differentiation_from_previous": "qué aprendiste o cambiaste respecto a IAMOs anteriores",
  "next_step": "acción externa concreta de mayor valor",
  "revenue_claim_eur": "0.00",
  "notes": "riesgos, supuestos o aprendizaje; indicá qué rutas del playbook consideraste si fueron relevantes"
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
            fh.write(f"payment_reference={payment_reference}\n")

    print(name)


if __name__ == "__main__":
    main()
