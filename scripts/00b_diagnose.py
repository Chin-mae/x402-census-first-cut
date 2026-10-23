"""Diagnose: full response bodies from the remaining candidate endpoints,
and whether mainnet.base.org answers a SMALL eth_getLogs range."""
import json
import requests

SEED = "0x13db4caf175f23f1429c2df6b333350c24705192"
USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
PAD = "0x" + "0" * 24 + SEED[2:]


def call(url, payload, timeout=45):
    try:
        r = requests.post(url, json=payload, timeout=timeout)
        return r.text[:300]
    except Exception as e:
        return f"EXC {str(e)[:200]}"


bn = {"jsonrpc": "2.0", "id": 1, "method": "eth_blockNumber", "params": []}
print("1rpc blockNumber:", call("https://1rpc.io/base", bn))
print("blockpi blockNumber:", call("https://base.blockpi.network/v1/rpc/public", bn))
print("llamarpc blockNumber:", call("https://base.llamarpc.com", bn, 60))
print("publicnode blockNumber:", call("https://base-rpc.publicnode.com", bn, 60))

# mainnet.base.org: small getLogs range
latest_txt = call("https://mainnet.base.org", bn)
print("base.org blockNumber:", latest_txt)
try:
    latest = int(json.loads(latest_txt)["result"], 16)
except Exception:
    latest = None
if latest:
    import json
    small = {"jsonrpc": "2.0", "id": 1, "method": "eth_getLogs",
             "params": [{"address": USDC, "topics": [TOPIC, PAD],
                         "fromBlock": hex(latest - 2000), "toBlock": hex(latest)}]}
    print("base.org getLogs 2k recent:", call("https://mainnet.base.org", small))
    med = {"jsonrpc": "2.0", "id": 1, "method": "eth_getLogs",
           "params": [{"address": USDC, "topics": [TOPIC, PAD],
                       "fromBlock": hex(latest - 302400), "toBlock": hex(latest)}]}
    print("base.org getLogs 302k:", call("https://mainnet.base.org", med))
