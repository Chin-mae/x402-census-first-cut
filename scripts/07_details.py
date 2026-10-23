"""Detail cuts for the teardown: ring membership, self-loop address,
top recipients before/after adjustment, the seventh wallet's payer,
daily counts. Reads data/dataset.csv (post-filter) and payments_base."""
import csv
import json
from collections import Counter, defaultdict

rows = []
with open("../data/dataset.csv") as f:
    for r in csv.DictReader(f):
        r["amount_usdc"] = float(r["amount_usdc"])
        for k in ("closed_loop", "seller_funded_buyer", "single_day_sender"):
            r[k] = int(r[k])
        rows.append(r)

findings = json.load(open("../data/findings.json"))
print("== SCC members with the ChainWard six ==")
print(findings["chainward_six"]["scc_members_with_six"])
print("inflow senders to six:", findings["chainward_six"]["inflow_senders"])
print("outflow recipients of six:", findings["chainward_six"]["outflow_recipients"])
print()
print("== flagged SCCs ==")
for c in findings["sccs_flagged"]:
    print(f" size={c['size']} internal={c['internal_count']} vol={c['internal_volume']} "
          f"ext_in={c['external_inflow_count']}/{c['external_inflow_volume']} "
          f"out_vol={c['external_outflow_volume']}")
    print("   ", c["addresses"])
print()
print("== all multi SCCs (top 15 by internal volume) ==")
for c in findings["sccs_all_multi"][:15]:
    print(f" size={c['size']} internal={c['internal_count']} vol={c['internal_volume']} "
          f"ext_in_vol={c['external_inflow_volume']} share={c['external_inflow_share']}")
print()
selfpay = [r for r in rows if r["from"] == r["to"]]
sp = Counter((r["from"], r["facilitator"]) for r in selfpay)
print("== self-payments (from == to) ==", len(selfpay),
      "total $", round(sum(r["amount_usdc"] for r in selfpay), 2))
for (a, fac), n in sp.most_common(5):
    vol = sum(r["amount_usdc"] for r in selfpay if r["from"] == a)
    print(f"   {a} via {fac}: {n} payments, ${vol:.2f}")
print()
adj = [r for r in rows if not (r["closed_loop"] or r["seller_funded_buyer"]
                               or r["single_day_sender"])]
top_adj = Counter()
for r in adj:
    top_adj[r["to"]] += r["amount_usdc"]
print("== top recipients, adjusted set ==")
for a, v in top_adj.most_common(8):
    n = sum(1 for r in adj if r["to"] == a)
    print(f"   {a}: ${v:.2f} across {n} payments")
top_raw = Counter()
for r in rows:
    top_raw[r["to"]] += r["amount_usdc"]
print("== top recipients, raw set ==")
for a, v in top_raw.most_common(8):
    n = sum(1 for r in rows if r["to"] == a)
    print(f"   {a}: ${v:.2f} across {n} payments")
print()
daily = Counter(r["timestamp"][:10] for r in rows)
print("== payments per UTC day (all facilitators in dataset) ==")
for d in sorted(daily):
    vol = sum(r["amount_usdc"] for r in rows if r["timestamp"][:10] == d)
    print(f"   {d}: {daily[d]} payments, ${vol:.2f}")
print()
sizes = sorted(r["amount_usdc"] for r in rows)
import statistics
print("payment size: median", statistics.median(sizes),
      "mean", round(statistics.mean(sizes), 4),
      "p90", sizes[int(0.9 * len(sizes))], "max", sizes[-1])
small = [r for r in rows if r["amount_usdc"] <= 0.10]
print(f"payments <= $0.10: {len(small)} ({len(small)/len(rows):.1%} of count), "
      f"${sum(r['amount_usdc'] for r in small):.2f} of volume")
