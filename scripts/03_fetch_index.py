"""Fetch x402 payment-index rows from x402scan's public tRPC API (no key).

Endpoint: GET https://www.x402scan.com/api/trpc/public.transfers.list
Input:  {"json": {chain, timeframe (days), facilitatorIds, sorting,
                  pagination: {page, page_size}}}
Output rows carry: sender (payer), recipient (payee), amount (raw, 6dp),
block_timestamp, tx_hash, transaction_from (facilitator address),
facilitator_id, log_index. Raw JSON is saved per facilitator so every
downstream number reconciles to a file on disk.
"""
import json
import sys
import time
import urllib.parse
import requests

API = "https://www.x402scan.com/api/trpc/public.transfers.list"
PAGE_SIZE = 100


def fetch_facilitator(fid, days=7):
    items = []
    page = 0
    while True:
        payload = {
            "chain": "base",
            "timeframe": days,
            "facilitatorIds": [fid],
            "sorting": {"id": "block_timestamp", "desc": True},
            "pagination": {"page": page, "page_size": PAGE_SIZE},
        }
        url = API + "?input=" + urllib.parse.quote(json.dumps({"json": payload}))
        for attempt in range(6):
            try:
                r = requests.get(url, timeout=90,
                                 headers={"user-agent": "Mozilla/5.0"})
                if r.status_code == 200:
                    break
                print(f"  {fid} page {page}: HTTP {r.status_code}, retry")
            except Exception as e:
                print(f"  {fid} page {page}: {e}, retry")
            time.sleep(3 * (attempt + 1))
        else:
            raise RuntimeError(f"failed {fid} page {page}")
        data = r.json()["result"]["data"]["json"]
        items.extend(data["items"])
        if page % 20 == 0:
            print(f"  {fid}: page {page}, rows so far {len(items)}")
        if not data["hasNextPage"]:
            break
        page += 1
        time.sleep(0.3)
    return items


def main():
    fids = sys.argv[1:] or ["mrdn"]
    for fid in fids:
        print(f"fetching {fid} ...")
        t0 = time.time()
        items = fetch_facilitator(fid)
        out = f"../data/index_{fid}_7d_raw.json"
        with open(out, "w") as f:
            json.dump({"facilitator_id": fid, "fetched_at_utc": time.strftime(
                "%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "rows": items}, f)
        ts = [i["block_timestamp"] for i in items]
        print(f"{fid}: {len(items)} rows in {time.time()-t0:.0f}s, "
              f"window {min(ts)} to {max(ts)} -> {out}")


if __name__ == "__main__":
    main()
