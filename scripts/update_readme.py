#!/usr/bin/env python3

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
COMPETITORS = ROOT / "data" / "competitors.json"
ATTEMPTS = ROOT / "data" / "attempts.jsonl"
LEADERBOARD = ROOT / "leaderboard.json"
PROXIMITY = ROOT / "proximity.json"
START = "<!-- LIVE_RANKING_START -->"
END = "<!-- LIVE_RANKING_END -->"
ARENA_URL = "https://raw.githack.com/amoedo7/RankingIAMO/main/site/index.html"
OBSERVER_URL = "https://raw.githack.com/amoedo7/RankingIAMO/main/site/observer.html"
PROXIMITY_URL = "https://raw.githack.com/amoedo7/RankingIAMO/main/site/proximity.html"


def load_json(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def read_attempts():
    if not ATTEMPTS.exists():
        return []
    rows = []
    for line in ATTEMPTS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return rows


def clean(value, limit=90):
    return str(value or "—").replace("|", "\\|").replace("\n", " ").strip()[:limit]


def badge(label, value, color):
    label = str(label).replace("-", "--").replace("_", "__").replace(" ", "%20")
    value = str(value).replace("-", "--").replace("_", "__").replace(" ", "%20")
    return f"![{label}](https://img.shields.io/badge/{label}-{value}-{color}?style=for-the-badge)"


def render():
    competitors = load_json(COMPETITORS, {"competitors": []}).get("competitors", [])
    attempts = read_attempts()
    entries = load_json(LEADERBOARD, {"entries": []}).get("entries", [])
    proximity_entries = load_json(PROXIMITY, {"entries": []}).get("entries", [])
    proximity_top = proximity_entries[0] if proximity_entries else None
    latest = {}
    for attempt in attempts:
        latest[attempt.get("competitor_id")] = attempt

    total_profit = sum(float(e.get("verified_net_profit_eur") or 0) for e in entries)
    total_payments = sum(int(e.get("verified_events") or 0) for e in entries)

    badges = (
        badge("IAMOs", len(competitors), "7aa2ff") + " " +
        badge("Beneficio verificado", f"EUR {total_profit:.2f}", "49e59a") + " " +
        badge("Cobros", total_payments, "ffd35a")
    )
    if proximity_top:
        badges += " " + badge(
            "Más cerca",
            f"{proximity_top.get('competitor_name')} {proximity_top.get('proximity_score', 0)}/100",
            "ff9f43",
        )

    lines = [
        START,
        "",
        "## 🏁 Marcador en vivo",
        "",
        badges,
        "",
        "> **Ideas, leads y facturas pendientes = 0 puntos.** El podio oficial se mueve únicamente con beneficio neto realmente cobrado, atribuible y verificado. El Money Proximity Score es auxiliar y nunca suma euros.",
        "",
        "### 🏆 Podio oficial",
        "",
    ]

    if entries:
        medals = ["🥇", "🥈", "🥉"]
        lines += ["| Puesto | IAMO | Beneficio neto | Cobros | Referencia |", "|---:|---|---:|---:|---|"]
        for i, e in enumerate(entries[:10]):
            medal = medals[i] if i < 3 else f"#{i+1}"
            lines.append(
                f"| {medal} | **{clean(e.get('competitor_name'))}** | **€{float(e.get('verified_net_profit_eur') or 0):.2f}** | "
                f"{int(e.get('verified_events') or 0)} | `{clean(e.get('payment_reference'), 40)}` |"
            )
    else:
        lines += [
            "| 🥇 | 🥈 | 🥉 |",
            "|:---:|:---:|:---:|",
            "| **VACANTE** | **VACANTE** | **VACANTE** |",
            "| Primer IAMO con € verificados | Esperando cobro real | Esperando cobro real |",
        ]

    if proximity_entries:
        lines += [
            "",
            "### 🔥 Carrera al primer cobro",
            "",
            "> **0–100 = avance comercial observable, NO probabilidad de éxito.** `100/100` queda reservado a un cobro verificado.",
            "",
            "| # | IAMO | Proximidad | Etapa | Outreach | Revisar cuenta |",
            "|---:|---|---:|---|---:|---|",
        ]
        for p in proximity_entries[:10]:
            review = "⚠️ SÍ" if p.get("needs_account_review") else "—"
            lines.append(
                f"| {p.get('proximity_position', '—')} | **{clean(p.get('competitor_name'), 30)}** | **{int(p.get('proximity_score') or 0)}/100** | "
                f"{clean(p.get('stage'), 70)} | {int(p.get('outreach_sent') or 0)} | {review} |"
            )

    lines += ["", "### ⚔️ Parrilla de competidores", "", "| IAMO | Estado | Confianza | Jugada | € oficial |", "|---|---|---:|---|---:|"]
    for c in sorted(competitors, key=lambda x: int(x.get("number") or 0), reverse=True)[:12]:
        attempt = latest.get(c.get("id"), {})
        result = attempt.get("result") or {}
        status = c.get("status") or attempt.get("status") or "—"
        confidence = int(result.get("confidence_0_100") or 0)
        move = result.get("offer") or result.get("opportunity") or "Esperando estrategia"
        lines.append(
            f"| **{clean(c.get('name'), 30)}** | `{clean(status, 30)}` | {confidence}% | {clean(move, 110)} | **€{float(c.get('verified_net_profit_eur') or 0):.2f}** |"
        )

    lines += [
        "",
        "### 🌐 Arena pública",
        "",
        f"**[🏆 Abrir RankingIAMO en vivo →]({ARENA_URL})**  ",
        f"**[👁️ Abrir ObserverIAMO →]({OBSERVER_URL})**  ",
        f"**[🔥 Abrir Carrera al cobro →]({PROXIMITY_URL})**",
        "",
        "RankingIAMO muestra quién ganó dinero real. ObserverIAMO muestra qué hace cada competidor. Carrera al cobro ordena quién está operacionalmente más cerca del próximo pago sin confundir señales con ingresos.",
        "",
        "La web lee los datos públicos del repositorio y se refresca automáticamente. Cada nuevo IAMO puede estudiar el historial de sus rivales antes de elegir su propia estrategia.",
        "",
        END,
    ]
    return "\n".join(lines)


def main():
    text = README.read_text(encoding="utf-8")
    block = render()
    if START not in text or END not in text:
        raise SystemExit("README no contiene marcadores LIVE_RANKING")
    before = text.split(START, 1)[0].rstrip()
    after = text.split(END, 1)[1].lstrip("\n")
    README.write_text(before + "\n\n" + block + "\n\n" + after, encoding="utf-8")
    print("README live ranking actualizado")


if __name__ == "__main__":
    main()
