"""Round 3: more keyless endpoints, and publicnode with a small recent range."""
import json
import requests

SEED = "0x13db4caf175f23f1429c2df6b333350c24705192"
USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
PAD = "0x" + "0" * 24 + SEED[2:]

URLS = [
    "https://base.gateway.tenderly.co",
    "https://rpc.ankr.com/base",
    "https://base-pokt.nodies.app",
    "https://rpc.notadegen.com/base",
    "https://base.api.onfinality.io/public",
    "https://base-rpc.publicnode.com",
]


def call(url, payload, timeout=30):
    try:
        r = requests.post(url, json=payload, timeout=timeout)
        return r.text[:220]
    except Exception as e:
        return f"EXC {str(e)[:160]}"


bn = {"jsonrpc": "2.0", "id": 1, "method": "eth_blockNumber", "params": []}
for url in URLS:
    txt = call(url, bn)
    print(url, "blockNumber:", txt)
    try:
        latest = int(json.loads(txt)["result"], 16)
    except Exception:
        continue
    small = {"jsonrpc": "2.0", "id": 1, "method": "eth_getLogs",
             "params": [{"address": USDC, "topics": [TOPIC, PAD],
                         "fromBlock": hex(latest - 2000), "toBlock": hex(latest)}]}
    print(url, "getLogs 2k:", call(url, small))
    hist = {"jsonrpc": "2.0", "id": 1, "method": "eth_getLogs",
            "params": [{"address": USDC, "topics": [TOPIC, PAD],
                        "fromBlock": hex(latest - 302400), "toBlock": hex(latest - 300000)}]}
    print(url, "getLogs hist 2.4k slice 7d back:", call(url, hist))
