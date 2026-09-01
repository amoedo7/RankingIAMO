import csv
from collections import Counter
from statistics import mean

NEGATIVE_KEYWORDS = [
    'malo', 'terrible', 'lento', 'incorrecto', 'molesto', 'problema',
    'pésimo', 'horrible', 'poca calidad', 'espera', 'peor', 'delayed', 'angry'
]


def load_rows(path):
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def summarize(rows):
    if not rows:
        return {
            'total_reviews': 0,
            'avg_rating': 0.0,
            'negative_mentions': 0,
            'top_risks': [],
            'rank_change': 0,
            'new_review_days': 0,
        }

    ratings = [float(r['rating']) for r in rows if r.get('rating')]
    text_blob = ' '.join((r.get('review', '') or '').lower() for r in rows)
    negative_mentions = sum(1 for kw in NEGATIVE_KEYWORDS if kw in text_blob)

    top_risks = []
    for kw in NEGATIVE_KEYWORDS:
        if kw in text_blob:
            top_risks.append(kw)

    rank_positions = [int(r['ranking_position']) for r in rows if r.get('ranking_position')]
    rank_change = 0
    if rank_positions:
        rank_change = rank_positions[-1] - rank_positions[0]

    return {
        'total_reviews': len(rows),
        'avg_rating': round(mean(ratings), 2) if ratings else 0.0,
        'negative_mentions': negative_mentions,
        'top_risks': top_risks[:5],
        'rank_change': rank_change,
        'new_review_days': len({r['date'] for r in rows if r.get('date')}),
    }


def main():
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else 'sample_reviews.csv'
    rows = load_rows(path)
    result = summarize(rows)
    print('Resumen del piloto GBP')
    print(f"Total de reseñas: {result['total_reviews']}")
    print(f"Valoración media: {result['avg_rating']}")
    print(f"Menciones negativas: {result['negative_mentions']}")
    print(f"Riesgos detectados: {', '.join(result['top_risks']) or 'ninguno'}")
    print(f"Cambio de posición: {result['rank_change']}")
    print(f"Días con reseña nueva: {result['new_review_days']}")


if __name__ == '__main__':
    main()