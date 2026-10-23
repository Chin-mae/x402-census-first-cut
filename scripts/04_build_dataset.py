"""Merge the raw x402scan index pulls into one payments table.

Window rule (deterministic, stated in methodology.md): keep rows with
block_timestamp >= 2026-10-16T16:08:00Z. Each facilitator pull used the
API's trailing-7-day window at fetch times between 15:56 and ~16:30 UTC
on 23 Oct 2026, so a uniform start edge at 16:08 on 16 Oct makes the
start identical for every facilitator. The end edge is as indexed at
fetch time (per-facilitator max timestamps are reported by the analysis).
Amounts: the index stores raw USDC units (6 decimals); the verified
receipt sample shows the amount is the DELIVERED leg (what the
recipient received).
"""
import csv
import glob
import json

START = "2026-10-16T16:08:00"
FACILITATOR_NAMES = {
    "mrdn": "Meridian",
    "ultravioletadao": "Ultravioleta DAO",
    "payAI": "PayAI",
    "coinbase": "Coinbase CDP",
}

rows = []
for path in sorted(glob.glob("../data/index_*_7d_raw.json")):
    with open(path) as f:
        blob = json.load(f)
    for r in blob["rows"]:
        ts = r["block_timestamp"].replace(".000Z", "").replace("Z", "")
        if ts < START:
            continue
        rows.append({
            "timestamp": ts + "Z",
            "tx_hash": r["tx_hash"],
            "from": r["sender"],
            "to": r["recipient"],
            "amount_usdc": r["amount"] / 1e6,
            "facilitator": FACILITATOR_NAMES.get(r["facilitator_id"],
                                                 r["facilitator_id"]),
            "facilitator_id": r["facilitator_id"],
            "tx_from": r["transaction_from"],
            "log_index": r["log_index"],
        })

rows.sort(key=lambda x: x["timestamp"])
with open("../data/payments_base.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print(f"{len(rows)} rows after window trim")
from collections import Counter
print(Counter(r["facilitator"] for r in rows))
