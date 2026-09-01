# Webhook Reliability Starter Kit

A minimal but usable MVP for small SaaS teams and agencies that need a reliable webhook intake layer.

## What it includes
- HMAC signature validation
- Event deduplication with idempotency keys
- Retry queue for failed deliveries
- Dead-letter log for malformed payloads
- Simple payload normalization helper
- Local demo server with health/check endpoints

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export WEBHOOK_SECRET=change-me
export TARGET_URL=https://example.com/webhook-target
python webhook_relay.py
```

Then send a POST to:

```bash
curl -X POST http://localhost:5000/webhook/stripe \
  -H 'Content-Type: application/json' \
  -H 'X-Signature: demo-signature' \
  -d '{"id":"evt_123","type":"invoice.paid","data":{"object":{"id":"in_123"}}}'
```

## Deliverable notes
This package is designed as a starter for a fixed-scope implementation. It is intentionally narrow: receiving, validating, deduplicating, and retrying webhook events without making a broad platform promise.

## Reference
RANK-IAMO512