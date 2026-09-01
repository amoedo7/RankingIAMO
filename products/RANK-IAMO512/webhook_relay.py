import hashlib
import hmac
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

QUEUE_DIR = Path(__file__).resolve().parent / 'data'
QUEUE_DIR.mkdir(exist_ok=True)
QUEUE_PATH = QUEUE_DIR / 'webhook_queue.jsonl'
SEEN_PATH = QUEUE_DIR / 'seen_events.json'


def load_seen_events() -> set:
    if not SEEN_PATH.exists():
        return set()
    try:
        with SEEN_PATH.open('r', encoding='utf-8') as fh:
            data = json.load(fh)
            return set(data.get('events', []))
    except Exception:
        return set()


def save_seen_events(events: set):
    with SEEN_PATH.open('w', encoding='utf-8') as fh:
        json.dump({'events': sorted(events)}, fh)


def verify_signature(payload: bytes, provided: Optional[str], secret: str) -> bool:
    if not provided:
        return False
    expected = hmac.new(secret.encode('utf-8'), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(provided, expected)


def dedupe_event(event_id: str, seen: set) -> bool:
    if event_id in seen:
        return True
    seen.add(event_id)
    save_seen_events(seen)
    return False


def append_queue(event: Dict[str, Any]):
    with QUEUE_PATH.open('a', encoding='utf-8') as fh:
        fh.write(json.dumps(event, ensure_ascii=False) + '\n')


def normalize_event(source: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    event_id = payload.get('id') or payload.get('event_id') or f'{source}-{int(time.time()*1000)}'
    return {
        'source': source,
        'event_id': event_id,
        'type': payload.get('type', 'unknown'),
        'received_at': int(time.time()),
        'status': 'received',
        'data': payload.get('data', payload),
    }


@app.get('/health')
def health():
    return jsonify({'status': 'ok', 'queue_path': str(QUEUE_PATH)})


@app.post('/webhook/<source>')
def handle_webhook(source: str):
    secret = os.getenv('WEBHOOK_SECRET', 'change-me')
    raw_body = request.get_data()
    provided_sig = request.headers.get('X-Signature')

    if not verify_signature(raw_body, provided_sig, secret):
        return jsonify({'status': 'rejected', 'reason': 'invalid_signature'}), 401

    try:
        body = json.loads(raw_body.decode('utf-8'))
    except Exception:
        body = {'raw': raw_body.decode('utf-8', errors='replace')}

    event_id = body.get('id') or body.get('event_id') or f'{source}-{int(time.time()*1000)}'
    seen_events = load_seen_events()

    if dedupe_event(event_id, seen_events):
        return jsonify({'status': 'duplicate', 'event_id': event_id})

    normalized = normalize_event(source, body)
    append_queue(normalized)

    target_url = os.getenv('TARGET_URL')
    if target_url:
        try:
            response = requests.post(
                target_url,
                json={
                    'event_id': normalized['event_id'],
                    'type': normalized['type'],
                    'source': normalized['source'],
                    'payload': normalized['data'],
                },
                timeout=10,
            )
            response.raise_for_status()
            normalized['delivery_status'] = 'delivered'
        except Exception as exc:
            normalized['delivery_status'] = 'failed'
            normalized['error'] = str(exc)
            append_queue({'status': 'dead_letter', 'event_id': normalized['event_id'], 'error': str(exc)})
    else:
        normalized['delivery_status'] = 'queued_only'

    append_queue(normalized)
    return jsonify({'status': 'accepted', 'event_id': event_id})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)