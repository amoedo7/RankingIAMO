#!/usr/bin/env python3

import json
from pathlib import Path
from mentor_context import build_mentor_context

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "runtime"
IDENTITY = RUNTIME / "identity.json"
PROMPT = RUNTIME / "prompt.txt"


def main():
    identity = json.loads(IDENTITY.read_text(encoding="utf-8"))
    number = int(identity["number"])
    context = build_mentor_context(number)
    RUNTIME.mkdir(parents=True, exist_ok=True)
    (RUNTIME / "mentor_context.json").write_text(
        json.dumps(context, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    cases = context.get("mentor_cases", [])
    case_lines = []
    for case in cases:
        case_lines.append(
            f"- {case.get('name')}: {case.get('reported_result')} LECCION: {case.get('lesson')} FUENTE: {case.get('source')}"
        )
    cases_text = "\n".join(case_lines) or "- No hay casos cargados en esta ronda."

    neighbors = context.get("agent_commons", {}).get("wealthy_neighbors", [])
    neighbor_text = "\n".join(
        f"- {n.get('name')}: {n.get('economic_signal')} — estudiá {n.get('study')}"
        for n in neighbors[:5]
    ) or "- Sin vecinos económicos cargados."

    messages = context.get("recent_agent_commons_messages", [])[-10:]
    messages_text = "\n".join(
        f"- [{m.get('author','?')}] {m.get('message','')}"
        for m in messages
    ) or "- Agent Commons todavía no tiene mensajes útiles."

    addition = f"""

# TU ENTORNO ECONOMICO — MONEY MENTORS

No estás aislado. RankingIAMO mantiene `data/real_ai_money_cases.json`, una biblioteca de casos públicos donde productos, empresas o sistemas basados en IA generaron ingresos, captaron capital o demostraron un mecanismo económico relevante. También incluye fracasos reales para evitar repetirlos.

Estos son tres mentores rotativos para IAMO{number}:

{cases_text}

No copies cifras ni afirmes que ese dinero es tuyo. Extraé el mecanismo: quién paga, por qué paga, qué se entrega, cómo se distribuye, qué retiene al cliente y qué puede validarse con coste cero.

# IAMO AGENT COMMONS

Tenés un canal compartido en `network/board.jsonl`. Los IAMOs pueden dejar ahí señales, necesidades, ofertas y aprendizajes estructurados para que los siguientes no empiecen de cero.

Vecinos económicos que vale la pena estudiar:

{neighbor_text}

Mensajes recientes del Commons:

{messages_text}

El mapa completo está en `network/agent_commons.json`. Incluye A2A como estándar de comunicación entre agentes y Virtuals ACP como mercado de referencia de agent-to-agent commerce. ACP está en modo **observe-only** para RankingIAMO mientras no exista una wallet y presupuesto separados explícitamente autorizados. Estudiar agentes con capital no te autoriza a tocar sus activos, impersonarlos ni eludir permisos.

Principio social: rodeate de sistemas que ya resuelven problemas por los que alguien paga. Copiá mecanismos, no humo.

"""

    with PROMPT.open("a", encoding="utf-8") as fh:
        fh.write(addition)
        fh.write("\n# CONTEXTO MONEY-MENTOR MACHINE-READABLE\n")
        fh.write(json.dumps(context, ensure_ascii=False, indent=2))
        fh.write("\n")

    print(f"IAMO{number}: prompt enriquecido con {len(cases)} money mentors y Agent Commons")


if __name__ == "__main__":
    main()
