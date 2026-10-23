"""Probe: define the 7-day window from chain timestamps and pull every USDC
transfer touching the ChainWard seed wallet 0x13db4caf... in that window.
Counterparties in the output identify the Meridian settlement contract and
the other five loop wallets (full addresses come from the logs themselves).
"""
import json
import sys
from collections import Counter

sys.path.insert(0, ".")
from rpc import rpc, get_logs, pad_addr, block_ts, USDC, TRANSFER_TOPIC

SEED = "0x13db4caf175f23f1429c2df6b333350c24705192"

latest = int(rpc("eth_blockNumber", []), 16)
# 7 days at 2s blocks = 302400 blocks; exact timestamps read from chain below.
end_block = latest
start_block = latest - 302400
print("latest block", latest, "ts", block_ts(latest))
print("start block", start_block, "ts", block_ts(start_block))

logs_out = get_logs(USDC, [TRANSFER_TOPIC, pad_addr(SEED)], start_block, end_block)
logs_in = get_logs(USDC, [TRANSFER_TOPIC, None, pad_addr(SEED)], start_block, end_block)
print("transfers out of seed:", len(logs_out))
print("transfers into seed:", len(logs_in))

cp_out = Counter()
cp_in = Counter()
for lg in logs_out:
    cp_out["0x" + lg["topics"][2][26:]] += 1
for lg in logs_in:
    cp_in["0x" + lg["topics"][1][26:]] += 1
print("top counterparties OUT (seed pays):")
for a, c in cp_out.most_common(12):
    print(" ", a, c)
print("top counterparties IN (seed receives):")
for a, c in cp_in.most_common(12):
    print(" ", a, c)

with open("../data/seed_logs.json", "w") as f:
    json.dump({"start_block": start_block, "end_block": end_block,
               "start_ts": block_ts(start_block), "end_ts": block_ts(end_block),
               "logs_out": logs_out, "logs_in": logs_in}, f)
print("saved ../data/seed_logs.json")
