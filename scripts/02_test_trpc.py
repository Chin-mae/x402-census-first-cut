"""Probe x402scan's public tRPC transfers.list endpoint (no auth)."""
import json
import urllib.parse
import requests

BASE = "https://www.x402scan.com/api/trpc/public.transfers.list"


def probe(payload):
    url = BASE + "?input=" + urllib.parse.quote(json.dumps({"json": payload}))
    r = requests.get(url, timeout=60, headers={"user-agent": "Mozilla/5.0"})
    print("status", r.status_code)
    txt = r.text
    print(txt[:1500])
    return txt


probe({
    "chain": "base",
    "timeframe": 7,
    "facilitatorIds": ["mrdn"],
    "sorting": {"id": "block_timestamp", "desc": True},
    "page": 0,
    "page_size": 3,
})
