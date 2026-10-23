"""Apply the published filters to payments_base.csv and write the final
dataset.csv (with flag columns) plus findings.json.

Filters (rules stated before figures, per methodology lock 3):
F1 closed_loop: strongly connected components (SCCs) of the directed
   payment graph. A payment is flagged if both endpoints sit in the same
   SCC and that SCC has >= 20 internal payments, >= $100 internal
   volume, and inflow from outside the SCC < 1% of (internal volume +
   inflow volume). An SCC is used because circulation requires a
   directed cycle; a weakly connected component always has zero
   boundary flow by construction and cannot be tested.
F2 seller_funded_buyer: a payment s -> r is flagged if the recipient r
   funded the sender s inside the window, either directly (an r -> s
   payment exists) or through one intermediary (r -> x -> s payments
   exist). In-index signature only: funding that moves as plain
   (non-x402) USDC transfers is not in this dataset, so F2 is a floor.
F3 single_day_sender: a payment is flagged if its sender appears on
   exactly one UTC calendar date in the window (Chainalysis's stated
   exclusion, applied to the sender side).
"""
import csv
import json
import sys
from collections import defaultdict

sys.setrecursionlimit(100000)

rows = []
with open("../data/payments_base.csv") as f:
    for r in csv.DictReader(f):
        r["amount_usdc"] = float(r["amount_usdc"])
        rows.append(r)

# ---------- directed graph + SCC (iterative Tarjan) ----------
adj = defaultdict(set)
nodes = set()
for r in rows:
    adj[r["from"]].add(r["to"])
    nodes.update([r["from"], r["to"]])
for n in nodes:
    adj.setdefault(n, set())

index_counter = [0]
stack = []
lowlink = {}
index_of = {}
on_stack = defaultdict(bool)
sccs = []

for root in nodes:
    if root in index_of:
        continue
    work = [(root, iter(sorted(adj[root])))]
    index_of[root] = lowlink[root] = index_counter[0]
    index_counter[0] += 1
    stack.append(root)
    on_stack[root] = True
    while work:
        node, it = work[-1]
        advanced = False
        for succ in it:
            if succ not in index_of:
                index_of[succ] = lowlink[succ] = index_counter[0]
                index_counter[0] += 1
                stack.append(succ)
                on_stack[succ] = True
                work.append((succ, iter(sorted(adj[succ]))))
                advanced = True
                break
            elif on_stack[succ]:
                lowlink[node] = min(lowlink[node], index_of[succ])
        if advanced:
            continue
        work.pop()
        if work:
            parent = work[-1][0]
            lowlink[parent] = min(lowlink[parent], lowlink[node])
        if lowlink[node] == index_of[node]:
            comp = []
            while True:
                w = stack.pop()
                on_stack[w] = False
                comp.append(w)
                if w == node:
                    break
            sccs.append(comp)

scc_id = {}
for i, comp in enumerate(sccs):
    for a in comp:
        scc_id[a] = i
self_loops = {r["from"] for r in rows if r["from"] == r["to"]}

scc_stats = {}
for i, comp in enumerate(sccs):
    if len(comp) < 2 and comp[0] not in self_loops:
        continue
    s = {"addresses": sorted(comp), "size": len(comp), "in_count": 0,
         "in_vol": 0.0, "ext_in_count": 0, "ext_in_vol": 0.0,
         "ext_out_count": 0, "ext_out_vol": 0.0}
    scc_stats[i] = s
for r in rows:
    sf, st = scc_id[r["from"]], scc_id[r["to"]]
    if sf == st and sf in scc_stats:
        scc_stats[sf]["in_count"] += 1
        scc_stats[sf]["in_vol"] += r["amount_usdc"]
    else:
        if sf in scc_stats:
            scc_stats[sf]["ext_out_count"] += 1
            scc_stats[sf]["ext_out_vol"] += r["amount_usdc"]
        if st in scc_stats:
            scc_stats[st]["ext_in_count"] += 1
            scc_stats[st]["ext_in_vol"] += r["amount_usdc"]

flagged_sccs = {}
for i, s in scc_stats.items():
    denom = s["in_vol"] + s["ext_in_vol"]
    s["ext_in_share"] = (s["ext_in_vol"] / denom) if denom else 0.0
    if s["in_count"] >= 20 and s["in_vol"] >= 100 and s["ext_in_share"] < 0.01:
        flagged_sccs[i] = s

for r in rows:
    sf = scc_id[r["from"]]
    r["closed_loop"] = int(sf == scc_id[r["to"]] and sf in flagged_sccs)

# ---------- F2 seller-funded-buyer ----------
out_edges = defaultdict(set)
in_edges = defaultdict(set)
pairs = set()
for r in rows:
    out_edges[r["from"]].add(r["to"])
    in_edges[r["to"]].add(r["from"])
    pairs.add((r["from"], r["to"]))

for r in rows:
    s, t = r["from"], r["to"]
    funded = (t, s) in pairs or bool((out_edges[t] & in_edges[s]) - {t, s})
    r["seller_funded_buyer"] = int(funded)

# ---------- F3 single-day sender ----------
days = defaultdict(set)
for r in rows:
    days[r["from"]].add(r["timestamp"][:10])
for r in rows:
    r["single_day_sender"] = int(len(days[r["from"]]) == 1)

# ---------- write final dataset ----------
fields = ["timestamp", "tx_hash", "from", "to", "amount_usdc", "facilitator",
          "closed_loop", "seller_funded_buyer", "single_day_sender"]
with open("../data/dataset.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    for r in rows:
        w.writerow({k: r[k] for k in fields})

# ---------- findings ----------
def agg(sub):
    return {"count": len(sub),
            "volume_usdc": round(sum(x["amount_usdc"] for x in sub), 2),
            "unique_senders": len({x["from"] for x in sub}),
            "unique_recipients": len({x["to"] for x in sub})}

findings = {"window": {"min_ts": min(r["timestamp"] for r in rows),
                       "max_ts": max(r["timestamp"] for r in rows)},
            "raw": agg(rows), "by_facilitator": {}}
for fac in sorted({r["facilitator"] for r in rows}):
    findings["by_facilitator"][fac] = agg([r for r in rows
                                           if r["facilitator"] == fac])
for flag in ["closed_loop", "seller_funded_buyer", "single_day_sender"]:
    findings[flag] = agg([r for r in rows if r[flag]])
for r in rows:
    r["any_flag"] = int(bool(r["closed_loop"] or r["seller_funded_buyer"]
                             or r["single_day_sender"]))
findings["flagged_any"] = agg([r for r in rows if r["any_flag"]])
findings["adjusted"] = agg([r for r in rows if not r["any_flag"]])

def scc_out(s):
    return {"addresses": s["addresses"], "size": s["size"],
            "internal_count": s["in_count"],
            "internal_volume": round(s["in_vol"], 2),
            "external_inflow_count": s["ext_in_count"],
            "external_inflow_volume": round(s["ext_in_vol"], 2),
            "external_inflow_share": round(s["ext_in_share"], 5),
            "external_outflow_volume": round(s["ext_out_vol"], 2)}

findings["sccs_flagged"] = sorted((scc_out(s) for s in flagged_sccs.values()),
                                  key=lambda c: -c["internal_volume"])
all_sccs = sorted((scc_out(s) for s in scc_stats.values()),
                  key=lambda c: -c["internal_volume"])
findings["sccs_all_multi"] = all_sccs[:15]
findings["scc_count_multi"] = len(scc_stats)

# ---------- ChainWard six-wallet sub-analysis ----------
SIX_PREFIXES = ["1cec447d", "fe8f511d", "a6a90366", "475436ef", "13db4caf",
                "e55eb84c"]
addr_by_prefix = {}
for r in rows:
    for a in (r["from"], r["to"]):
        addr_by_prefix.setdefault(a[2:10], a)
six = {addr_by_prefix[p] for p in SIX_PREFIXES if p in addr_by_prefix}
inside = [r for r in rows if r["from"] in six and r["to"] in six]
inflow = [r for r in rows if r["to"] in six and r["from"] not in six]
outflow = [r for r in rows if r["from"] in six and r["to"] not in six]
findings["chainward_six"] = {
    "addresses_found": sorted(six),
    "scc_of_six": sorted({scc_id[a] for a in six}),
    "scc_members_with_six": sorted(
        a for a in nodes if scc_id[a] in {scc_id[x] for x in six}),
    "internal": agg(inside),
    "inflow_from_outside": agg(inflow),
    "inflow_senders": sorted({r["from"] for r in inflow}),
    "outflow_to_outside": agg(outflow),
    "outflow_recipients": sorted({r["to"] for r in outflow}),
    "received_by_wallet": {a: round(sum(r["amount_usdc"] for r in rows
                                        if r["to"] == a), 2) for a in sorted(six)},
}
seventh = addr_by_prefix.get("c2204317")
if seventh:
    findings["chainward_seventh"] = {
        "address": seventh,
        "received": agg([r for r in rows if r["to"] == seventh]),
        "received_from": sorted({r["from"] for r in rows
                                 if r["to"] == seventh}),
        "sent": agg([r for r in rows if r["from"] == seventh]),
    }

# ---------- extra cuts for the write-up ----------
selfpay = [r for r in rows if r["from"] == r["to"]]
findings["self_payments"] = {
    "total": agg(selfpay),
    "flagged_any": agg([r for r in selfpay if r["any_flag"]]),
    "unflagged": agg([r for r in selfpay if not r["any_flag"]]),
}
findings["adjusted_by_facilitator"] = {
    fac: agg([r for r in rows if r["facilitator"] == fac and not r["any_flag"]])
    for fac in sorted({r["facilitator"] for r in rows})}
findings["flag_overlaps"] = {
    "closed_and_sfb": len([r for r in rows if r["closed_loop"]
                           and r["seller_funded_buyer"]]),
    "closed_only": len([r for r in rows if r["closed_loop"]
                        and not r["seller_funded_buyer"]
                        and not r["single_day_sender"]]),
    "sfb_only": len([r for r in rows if r["seller_funded_buyer"]
                     and not r["closed_loop"] and not r["single_day_sender"]]),
    "single_day_only": len([r for r in rows if r["single_day_sender"]
                            and not r["closed_loop"]
                            and not r["seller_funded_buyer"]]),
}
sizes = sorted(r["amount_usdc"] for r in rows)
import statistics
findings["size_distribution"] = {
    "median": statistics.median(sizes), "mean": round(statistics.mean(sizes), 4),
    "max": sizes[-1],
    "le_10c_count": len([s for s in sizes if s <= 0.10]),
    "le_10c_volume": round(sum(s for s in sizes if s <= 0.10), 2),
}

with open("../data/findings.json", "w") as f:
    json.dump(findings, f, indent=1)
print("raw", findings["raw"])
print("adjusted", findings["adjusted"])
print("flagged sccs", len(findings["sccs_flagged"]))
for c in findings["sccs_flagged"]:
    print("  size", c["size"], "in", c["internal_count"],
          round(c["internal_volume"], 2), "ext_in_share", c["external_inflow_share"])
print("six internal", findings["chainward_six"]["internal"],
      "inflow", findings["chainward_six"]["inflow_from_outside"])
