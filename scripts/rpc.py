"""Shared helpers for keyless public Base RPC access.

Endpoints tried in order. mainnet.base.org rate-limits eth_getLogs quickly
(error -32011 "request limit reached"), so calls rotate across public
endpoints and back off on limit errors. Range errors halve the chunk;
limit errors never do.
"""
import time
import requests

RPC_URLS = [
    "https://mainnet.base.org",
    "https://base-rpc.publicnode.com",
    "https://base.llamarpc.com",
    "https://base.drpc.org",
]
USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

_session = requests.Session()
_url_idx = 0


def _post(url, method, params):
    r = _session.post(url, json={"jsonrpc": "2.0", "id": 1,
                                 "method": method, "params": params},
                      timeout=60)
    return r.json()


def rpc(method, params, retries=8):
    global _url_idx
    last_err = None
    for attempt in range(retries):
        url = RPC_URLS[_url_idx % len(RPC_URLS)]
        try:
            j = _post(url, method, params)
            if "error" in j:
                msg = str(j["error"])
                last_err = msg
                if "limit" in msg.lower() or "rate" in msg.lower() or "429" in msg:
                    _url_idx += 1
                    time.sleep(3 * (attempt + 1))
                    continue
                raise RuntimeError(f"RPC error {method}: {j['error']}")
            return j["result"]
        except RuntimeError:
            raise
        except Exception as e:  # network error: rotate endpoint
            last_err = str(e)
            _url_idx += 1
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"RPC {method} failed after retries: {last_err}")


def pad_addr(addr):
    return "0x" + "0" * 24 + addr.lower().replace("0x", "")


def get_logs(address, topics, from_block, to_block, chunk=5000, pace=0.25):
    """Fetch eth_getLogs; halves chunk on range errors only."""
    out = []
    b = from_block
    size = chunk
    while b <= to_block:
        end = min(b + size - 1, to_block)
        try:
            logs = rpc("eth_getLogs", [{
                "address": address,
                "topics": topics,
                "fromBlock": hex(b),
                "toBlock": hex(end),
            }])
            out.extend(logs)
            b = end + 1
            if pace:
                time.sleep(pace)
        except RuntimeError as e:
            msg = str(e).lower()
            if "limit" in msg or "rate" in msg:
                time.sleep(20)
                continue
            if size <= 250:
                raise
            size //= 2
    return out


def block_ts(block):
    blk = rpc("eth_getBlockByNumber", [hex(block), False])
    return int(blk["timestamp"], 16)
