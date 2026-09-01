#!/usr/bin/env python3
import argparse
import csv
import html
from collections import Counter
from datetime import datetime


def parse_date(value):
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            pass
    return None


def sentiment_from_rating(rating):
    rating = float(rating)
    if rating >= 4.5:
        return "positivo"
    if rating >= 3.5:
        return "neutral"
    return "negativo"


def detect_risk(text):
    low_risk = ["gracias", "genial", "muy bien", "recomiendo", "excelente"]
    high_risk = ["espera", "descontento", "mal trato", "demora", "dolor", "falta de higiene", "fallo"]
    lowered = text.lower()
    if any(term in lowered for term in high_risk):
        return "alto"
    if any(term in lowered for term in low_risk):
        return "bajo"
    return "medio"


def main():
    parser = argparse.ArgumentParser(description="Genera un resumen de reseñas y riesgo para clínicas privadas.")
    parser.add_argument("csv_path")
    parser.add_argument("--out", default="dashboard.html")
    args = parser.parse_args()

    reviews = []
    with open(args.csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row:
                continue
            date = parse_date(row.get("date", ""))
            if row.get("text"):
                reviews.append({
                    "date": date,
                    "rating": float(row.get("rating", 0) or 0),
                    "text": row.get("text", "").strip(),
                    "source": row.get("source", "Google")
                })

    total_reviews = len(reviews)
    avg_rating = sum(r["rating"] for r in reviews) / total_reviews if total_reviews else 0
    sentiment_counts = Counter(sentiment_from_rating(r["rating"]) for r in reviews)
    risk_counts = Counter(detect_risk(r["text"]) for r in reviews)

    risk_items = []
    for review in reviews:
        if detect_risk(review["text"]) in {"alto", "medio"}:
            risk_items.append({
                "rating": review["rating"],
                "text": review["text"],
                "risk": detect_risk(review["text"])
            })

    html_out = f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>GBP Review Risk Monitor</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 30px; background: #f4f7fb; color: #1d2433; }}
    h1 {{ font-size: 36px; margin-bottom: 8px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin: 24px 0; }}
    .card {{ background: white; border-radius: 12px; padding: 16px; box-shadow: 0 8px 18px rgba(0,0,0,0.06); }}
    .label {{ font-size: 12px; color: #64748b; text-transform: uppercase; letter-spacing: 0.08em; }}
    .value {{ font-size: 28px; font-weight: bold; margin-top: 8px; }}
    table {{ width: 100%; border-collapse: collapse; background: white; }}
    th, td {{ padding: 12px; border-bottom: 1px solid #e5e7eb; text-align: left; }}
    .high {{ color: #b91c1c; font-weight: bold; }}
    .medium {{ color: #b45309; font-weight: bold; }}
    .low {{ color: #15803d; font-weight: bold; }}
  </style>
</head>
<body>
  <h1>GBP Review Risk Monitor</h1>
  <p>Resumen de reseñas de Google Business Profile para decidir respuestas prioritarias.</p>
  <div class="grid">
    <div class="card"><div class="label">Total reseñas</div><div class="value">{total_reviews}</div></div>
    <div class="card"><div class="label">Rating medio</div><div class="value">{avg_rating:.2f}</div></div>
    <div class="card"><div class="label">Positivas</div><div class="value">{sentiment_counts.get('positivo', 0)}</div></div>
    <div class="card"><div class="label">Negativas</div><div class="value">{sentiment_counts.get('negativo', 0)}</div></div>
  </div>

  <h2>Riesgo de reputación</h2>
  <table>
    <tr><th>Nivel</th><th>Conteo</th></tr>
    <tr><td class="high">Alto</td><td>{risk_counts.get('alto', 0)}</td></tr>
    <tr><td class="medium">Medio</td><td>{risk_counts.get('medio', 0)}</td></tr>
    <tr><td class="low">Bajo</td><td>{risk_counts.get('bajo', 0)}</td></tr>
  </table>

  <h2>Comentarios prioritarios</h2>
  <table>
    <tr><th>Riesgo</th><th>Rating</th><th>Comentario</th></tr>
    {''.join(f'<tr><td class="{('high' if item['risk']=='alto' else 'medium' if item['risk']=='medio' else 'low')}">{html.escape(item['risk'])}</td><td>{item['rating']}</td><td>{html.escape(item['text'])}</td></tr>' for item in risk_items[:10])}
  </table>
</body>
</html>
"""

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(html_out)

    print(f"Resumen generado: {args.out}")


if __name__ == "__main__":
    main()