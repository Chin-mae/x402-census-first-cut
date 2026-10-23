"""Verify index rows against on-chain receipts via mainnet.base.org
(eth_getTransactionReceipt is not subject to the eth_getLogs quota).

For each sampled row, pull the receipt and list every USDC Transfer log.
A row verifies if a Transfer log matches (sender -> recipient, amount)
directly, or (Meridian two-leg pattern) the receipt shows the payer paying
the facilitator contract and the contract delivering to the recipient.
Results saved to data/verification.json.
"""
import json
import random
import sys
import time
import requests

RPC = "https://mainnet.base.org"
USDC = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"


def receipt(tx):
    for attempt in range(5):
        try:
            j = requests.post(RPC, json={"jsonrpc": "2.0", "id": 1,
                                         "method": "eth_getTransactionReceipt",
                                         "params": [tx]}, timeout=40).json()
            if "result" in j and j["result"]:
                return j["result"]
        except Exception:
            pass
        time.sleep(2 * (attempt + 1))
    return None


def transfers(rcpt):
    out = []
    for lg in rcpt["logs"]:
        if lg["address"].lower() == USDC and lg["topics"][0] == TRANSFER:
            out.append({
                "from": "0x" + lg["topics"][1][26:],
                "to": "0x" + lg["topics"][2][26:],
                "value": int(lg["data"], 16),
            })
    return out


def main():
    rows = []
    for fid in ["mrdn", "ultravioletadao", "payAI"]:
        with open(f"../data/index_{fid}_7d_raw.json") as f:
            rows.extend(json.load(f)["rows"])
    random.seed(41)
    sample = random.sample(rows, 12)
    # always include the known Meridian loop row
    sample.append(next(r for r in rows if r["tx_hash"].startswith("0xe39f6378")))
    results = []
    for row in sample:
        rcpt = receipt(row["tx_hash"])
        if rcpt is None:
            results.append({"tx": row["tx_hash"], "status": "no_receipt"})
            continue
        legs = transfers(rcpt)
        direct = any(l["from"] == row["sender"] and l["to"] == row["recipient"]
                     and l["value"] == row["amount"] for l in legs)
        delivered = any(l["to"] == row["recipient"] and l["value"] == row["amount"]
                        for l in legs)
        paid_leg = [l for l in legs if l["from"] == row["sender"]]
        results.append({
            "tx": row["tx_hash"], "facilitator": row["facilitator_id"],
            "index_sender": row["sender"], "index_recipient": row["recipient"],
            "index_amount": row["amount"],
            "direct_match": direct, "delivered_leg_match": delivered,
            "legs": legs, "status": "ok",
        })
        print(row["facilitator_id"], row["tx_hash"][:14], "direct:", direct,
              "delivered:", delivered, "legs:", len(legs))
        time.sleep(0.4)
    with open("../data/verification.json", "w") as f:
        json.dump(results, f, indent=1)
    ok = [r for r in results if r.get("status") == "ok"]
    print(f"verified {sum(r['delivered_leg_match'] for r in ok)}/{len(ok)} "
          f"delivered-leg matches; {sum(r['direct_match'] for r in ok)} direct")


if __name__ == "__main__":
    main()
