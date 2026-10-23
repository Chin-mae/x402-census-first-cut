"""Test which keyless public Base endpoints answer a small eth_getLogs query."""
import requests

SEED = "0x13db4caf175f23f1429c2df6b333350c24705192"
USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
PAD = "0x" + "0" * 24 + SEED[2:]

URLS = [
    "https://mainnet.base.org",
    "https://base-rpc.publicnode.com",
    "https://base.llamarpc.com",
    "https://base.drpc.org",
    "https://base-mainnet.public.blastapi.io",
    "https://1rpc.io/base",
    "https://base.blockpi.network/v1/rpc/public",
    "https://endpoints.omniatech.io/v1/base/mainnet/public",
    "https://api.zan.top/node/v1/base/mainnet/public",
    "https://base.meowrpc.com",
]

for url in URLS:
    try:
        s = requests.Session()
        bn = s.post(url, json={"jsonrpc": "2.0", "id": 1, "method": "eth_blockNumber",
                               "params": []}, timeout=20).json()
        latest = int(bn["result"], 16)
        r = s.post(url, json={"jsonrpc": "2.0", "id": 1, "method": "eth_getLogs",
                              "params": [{"address": USDC,
                                          "topics": [TOPIC, PAD],
                                          "fromBlock": hex(latest - 100000),
                                          "toBlock": hex(latest)}]}, timeout=40).json()
        if "result" in r:
            print(f"OK   {url}  logs={len(r['result'])} over 100k blocks")
        else:
            print(f"ERR  {url}  {str(r.get('error'))[:110]}")
    except Exception as e:
        print(f"FAIL {url}  {str(e)[:110]}")
