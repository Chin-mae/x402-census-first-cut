"""How far back will publicnode serve eth_getLogs without a token?"""
import json
import requests

URL = "https://base-rpc.publicnode.com"
USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"


def call(payload, timeout=40):
    try:
        r = requests.post(URL, json=payload, timeout=timeout)
        return r.text[:200]
    except Exception as e:
        return f"EXC {str(e)[:160]}"


latest = int(json.loads(call({"jsonrpc": "2.0", "id": 1, "method": "eth_blockNumber",
                               "params": []}))["result"], 16)
print("latest", latest)
for back in [5000, 20000, 50000, 100000, 150000, 200000]:
    frm = latest - back
    p = {"jsonrpc": "2.0", "id": 1, "method": "eth_getLogs",
         "params": [{"address": USDC, "topics": [TOPIC],
                     "fromBlock": hex(frm), "toBlock": hex(frm + 1000)}]}
    print(f"back={back}:", call(p))
