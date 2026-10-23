# Methodology: first cut of an adjusted census of x402 payments on Base

Implements Concept 1 and methodology locks 1 to 3 of `thesis-brief-v2.md` at sample scale. Every figure in `teardown.md` reconciles to `data/dataset.csv` or is attributed to a named source. Prepared 23 October 2026.

## Unit of count (lock 1)

A payment is one row of the x402scan payment index for Base: a USDC transfer that the index attributes to a registered x402 resource and tags with a facilitator. Raw USDC transfers are never counted as x402 payments. The amount recorded is the delivered amount, what the recipient received. This was verified against on-chain receipts: for Meridian, which settles in two legs (payer to contract, contract to recipient), the index amount equals the second leg exactly; for PayAI and Ultravioleta DAO the settlement is a single direct transfer and matches exactly.

## Coverage

- Chain: Base only. Solana is excluded from this cut entirely (lock 4 staging).
- Window: rows with block timestamp at or after 2026-10-16T16:08:00Z, through each facilitator's latest indexed timestamp at fetch time. Latest timestamps in the dataset: 2026-10-23T15:54:53Z overall. The first and last UTC days are partial.
- Facilitators at row level (complete pulls): Meridian (index id `mrdn`), PayAI (`payAI`), Ultravioleta DAO (`ultravioletadao`). 11,435 payments.
- Coinbase CDP is excluded from the row-level dataset. The index's own aggregate endpoint reports 483,421 Coinbase CDP payments on Base for the same trailing seven days; at 100 rows per page that is about 4,800 paginated calls against an offset-paginated endpoint, which was not practical for this cut. Coinbase appears only as an attributed index aggregate, never in a filtered figure. The pull was attempted and stopped for this reason.
- All other facilitators in the index (about 30 configured) are also outside the row-level scope. Across every facilitator, the index's aggregate endpoint reports 567,142 Base payments worth $575,249.76 for the trailing seven days, queried 23 October 2026.
- Ultravioleta DAO's index lagged at fetch time: its latest indexed transfer is 2026-10-23T11:18:27Z, about four and a half hours behind the other two facilitators. Its window is therefore slightly shorter at the end edge.

## Address book (lock 2)

Facilitator settlement addresses are taken from x402scan's open source facilitator package (Merit Systems, `packages/external/facilitators/src/facilitators/` in the public `x402scan` repository, fetched 23 October 2026; the files are saved in `data/`):

- Meridian on Base: `0x3210d7b21bfe1083c9dddbe17e8f947c9029a584` (current) and `0x8e7769d440b3460b92159dd9c6d17302b036e2d6` (marked deprecated in the config). In the one Meridian payment verified on chain for this cut, settlement ran through the deprecated address, not the current one: the payer paid `0x8e7769d4` 23.411979 USDC and it delivered 23.177860 USDC to the recipient, keeping 0.234119 USDC, exactly 1 percent of the amount paid. Rows are attributed to Meridian by the index's facilitator tag, not by which contract submitted or settled the transaction.
- Ultravioleta DAO on Base: `0x103040545ac5031a11e8c03dd11324c7333a13c7`.
- PayAI on Base: eight addresses are listed in the config, four of them marked deprecated; rows are attributed by the index's facilitator tag (full list in `data/facilitator_payai.ts`).
- Cloudflare, named in the evidence pack's forensic sources, has no facilitator entry in the fetched config and no rows in this dataset.

## Data routes: what was tried, what worked

1. Public Base RPC, `eth_getLogs` (the specified first route). Failed. `https://mainnet.base.org` answered `eth_blockNumber` and `eth_getTransactionReceipt` throughout, but every `eth_getLogs` call, over ranges from 2,000 to 302,400 blocks, returned error -32011, "request limit reached", across the whole session. `https://base-rpc.publicnode.com` served `eth_getLogs` only for roughly the last 10,000 blocks; older ranges returned "Archive requests require a personal token". No account or token was created. `base.llamarpc.com`, `base.drpc.org`, `base-mainnet.public.blastapi.io`, `1rpc.io/base`, `base.blockpi.network`, `base.api.onfinality.io`, `base-pokt.nodies.app`, `rpc.notadegen.com`, `base.gateway.tenderly.co` and `rpc.ankr.com/base` timed out or failed through this environment's proxy.
2. Blockscout API for Base (`base.blockscout.com/api/v2`): HTTP 403, Cloudflare challenge, by direct request and by page fetch. Not used.
3. Routescan Etherscan-compatible API: responded "chain not supported" for Base. Not used.
4. Dune: no keyless public result endpoint was available to this cut. Not used.
5. x402scan public API (no key, no account). Worked. The row data comes from `GET https://www.x402scan.com/api/trpc/public.transfers.list` and the aggregates from `public.stats.overall`. The call shapes were read from the project's public source code (routers and zod schemas in the repository above). This is the index leg of the unit of count in lock 1.
6. Receipt verification: `eth_getTransactionReceipt` via `https://mainnet.base.org` worked. A random sample of 13 rows (seed 41, across all three facilitators and all days, plus one targeted Meridian row) was checked against receipts: 13 of 13 delivered legs match the index's sender, recipient and amount exactly. Results in `data/verification.json`.

Completeness cross-check: the rows pulled were summed and compared with the index's own aggregate endpoint queried minutes later. Ultravioleta DAO matches exactly (5,380 transactions, $1,270.1038). Meridian matches on count (810) with volume $17.65 higher in the aggregate, and PayAI differs by 4 transactions and $0.10, both consistent with the aggregate's trailing window sliding a few minutes past the row pull. The pull is treated as complete for the stated window.

## Filters (lock 3: rules and thresholds published with the amounts removed)

Applied to the payment graph built from `dataset.csv` (directed edges payer to recipient, weighted by delivered USDC).

- F1, closed loop. Compute the strongly connected components (SCCs) of the payment graph. A component is a closed loop if it has at least 20 internal payments, at least $100 of internal volume, and inflow from outside the component under 1 percent of (internal volume plus inflow volume). Every payment with both endpoints in a flagged component is flagged. An SCC is used because circulation requires a directed cycle; a weakly connected component has zero boundary flow by construction and cannot be tested against an inflow threshold. A single address paying itself counts as a component of size one when it has a self-loop.
- F2, seller-funded buyer. A payment from s to r is flagged if r funded s inside the window through indexed payments: directly (an r to s payment exists) or through one intermediary (payments r to x and x to s exist). This is an in-index signature only. Funding that moves as plain USDC transfers is not in this dataset, so F2 is a floor, not a measure of all seller-funded demand.
- F3, single-day sender. A payment is flagged if its sender appears on exactly one UTC calendar date in the window. This is Chainalysis's stated exclusion, applied to the sender side.

Amounts removed by each filter, and by their union, are reported in `teardown.md` and in `data/findings.json`. Self-payments (sender equals recipient) satisfy F2 by construction; they are also reported as their own line so the reader does not have to take the filter's word for them.

## Limitations

- Funding history before 16 October is invisible. A buyer funded by its seller before the window opens looks external. Closed-loop inflow shares are therefore upper bounds on openness in one direction only: a component flagged here received almost nothing from outside during the window, but this cut cannot show where its balances originally came from.
- The index is not the chain. ChainWard's cross-check (evidence D2) found the index holding 3,503 of 3,554 payments in one Meridian sample. Counts here are complete for the index and near-complete for these facilitators; they are not a chain-wide census.
- Amounts are delivered amounts. For Meridian, amounts paid are about 1 percent higher (the facilitator's fee). No paid-side figure is computed for the full dataset because only the delivered leg is indexed uniformly.
- Nothing in this dataset identifies who controls an address, whether a payment bought anything, or whether a recipient sells anything. Where the write-up says a seller shows no sign of selling, that absence is ChainWard's published finding, attributed to them, not a finding of this cut.

## Reproduction

Run from `first-cut/scripts/`:

1. `python3 03_fetch_index.py mrdn ultravioletadao payAI` writes `data/index_<id>_7d_raw.json`. (Coinbase is not in the list for the reason given under Coverage.)
2. `python3 04_build_dataset.py` applies the window trim and writes `data/payments_base.csv`.
3. `python3 05_analyze.py` applies F1 to F3 and writes `data/dataset.csv` and `data/findings.json`.
4. `python3 06_verify_receipts.py` repeats the receipt sample check (random seed 41) into `data/verification.json`.
5. `python3 07_details.py` prints the detail cuts quoted in the write-up.

Route probes are kept as `00_test_endpoints.py`, `00b_diagnose.py`, `00c_more_endpoints.py`, `00d_publicnode_horizon.py` and `02_test_trpc.py` so the failure record is inspectable.
