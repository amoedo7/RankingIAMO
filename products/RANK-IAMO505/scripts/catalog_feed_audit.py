#!/usr/bin/env python3
import csv
import sys
from collections import defaultdict


def audit_feed(csv_path):
    issues = []
    counts = defaultdict(int)
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        for row in reader:
            handle = (row.get('Handle') or '').strip()
            title = (row.get('Title') or '').strip()
            variant_title = (row.get('Variant Title') or '').strip()
            gtin = (row.get('GTIN') or '').strip()
            mpn = (row.get('MPN') or '').strip()
            image = (row.get('Image Src') or '').strip()
            product_type = (row.get('Product Type') or '').strip()

            counts[handle] += 1
            if not title:
                issues.append(f"Missing Title: {handle}")
            if not image:
                issues.append(f"Missing Image: {handle}")
            if not gtin and not mpn:
                issues.append(f"Missing GTIN/MPN: {handle}")
            if product_type and ' ' in product_type and product_type.strip() == product_type.strip().lower():
                issues.append(f"Low-quality product type: {handle}")
            if variant_title and variant_title.lower() in title.lower() and title.lower().count(variant_title.lower()) > 1:
                issues.append(f"Variant title duplicated in product title: {handle}")

    duplicates = [name for name, count in counts.items() if count > 1]
    if duplicates:
        issues.append(f"Duplicate handles detected: {', '.join(duplicates[:10])}")

    return sorted(set(issues))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: catalog_feed_audit.py <products.csv>')
        sys.exit(1)
    for issue in audit_feed(sys.argv[1]):
        print(issue)
    print(f'\nTotal issues: {len(audit_feed(sys.argv[1]))}')