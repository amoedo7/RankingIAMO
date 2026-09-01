import csv
import sys
from collections import Counter


def detect_issues(csv_path):
    issues = []
    with open(csv_path, newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        return {"total_rows": 0, "problems": ["El archivo no contiene filas válidas."]}

    title_counter = Counter()
    duplicate_titles = []
    rows_with_missing_image = []
    rows_with_missing_handle = []
    rows_with_missing_variant = []
    rows_with_missing_sku = []

    for row in rows:
        title = (row.get('Title') or '').strip()
        if title:
            title_counter[title] += 1
        if not row.get('Image Src'):
            rows_with_missing_image.append(row.get('Handle') or row.get('Title') or 'Fila sin identificador')
        if not row.get('Handle'):
            rows_with_missing_handle.append(row.get('Title') or 'Fila sin título')
        if not row.get('Variant Title'):
            rows_with_missing_variant.append(row.get('Title') or 'Fila sin título')
        if not row.get('SKU'):
            rows_with_missing_sku.append(row.get('Title') or 'Fila sin título')

    for title, count in title_counter.items():
        if count > 1:
            duplicate_titles.append((title, count))

    issues.extend([
        f"Total de filas: {len(rows)}",
        f"Títulos duplicados: {len(duplicate_titles)}",
        f"Filas sin imagen: {len(rows_with_missing_image)}",
        f"Filas sin handle: {len(rows_with_missing_handle)}",
        f"Filas sin variant title: {len(rows_with_missing_variant)}",
        f"Filas sin SKU: {len(rows_with_missing_sku)}",
    ])

    if duplicate_titles:
        issues.append("Duplicados detectados: " + ", ".join(f"{title} ({count})" for title, count in duplicate_titles[:10]))
    if rows_with_missing_image:
        issues.append("Ejemplos sin imagen: " + ", ".join(rows_with_missing_image[:10]))
    if rows_with_missing_handle:
        issues.append("Ejemplos sin handle: " + ", ".join(rows_with_missing_handle[:10]))
    if rows_with_missing_variant:
        issues.append("Ejemplos sin variant title: " + ", ".join(rows_with_missing_variant[:10]))
    if rows_with_missing_sku:
        issues.append("Ejemplos sin SKU: " + ", ".join(rows_with_missing_sku[:10]))

    return {"total_rows": len(rows), "problems": issues}


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Uso: python catalog_feed_audit.py archivo.csv')
        sys.exit(1)

    report = detect_issues(sys.argv[1])
    print('\n'.join(report['problems']))