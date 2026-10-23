# Counting what counts: agent payments on Base, adjusted

An adjusted census of x402 agent payments, first cut. Every x402 payment in the
x402scan index on Base through three facilitators (Meridian, PayAI, Ultravioleta DAO)
for one week, 16 to 23 October 2026: 11,435 payments, with three published filters
applied (closed loops, seller-funded buyers, single-day senders).

**Headline:** $24,670.70 settled raw. $5,612.69 after adjustment (value down 77.3%).
A nine-wallet closed loop accounts for 82.9% of one facilitator's week.

## Contents

- `data/dataset.csv` — all 11,435 payment rows with the three filter flags. Every
  figure in the note reconciles to this file.
- `methodology.md` — unit of count, facilitator address book, filter rules with
  thresholds, data-route log, limitations, reproduction commands.
- `scripts/` — the full pipeline (fetch, build, analyze, verify against on-chain
  receipts: 13 of 13 sampled rows matched exactly).

The note below is the write-up. It also names the largest case its own filters
miss, because an adjusted count that hides its largest miss is doing the thing it
accuses the raw count of doing.

---

# Counting what counts: agent payments on Base, adjusted

First cut. Scope: every x402 payment the x402scan index holds for Base through three facilitators, Meridian, PayAI and Ultravioleta DAO, from 16 October 2026, 16:08 UTC, to each facilitator's latest indexed transfer on 23 October 2026. The dataset is published with this note. Every figure below either comes out of that dataset or is attributed to the source that published it.

By Chinmay Gupta

## The headline

The index holds 11,435 payments for the week through these three facilitators, worth $24,670.70 delivered. Apply three filters, each published as a rule before any figure here was computed (closed loops, seller-funded buyers, single-day senders; the rules are in the methodology note), and 8,809 payments survive, worth $5,612.69.

The count falls by 23.0 percent. The money falls by 77.3 percent. The filters removed 2,626 payments and $19,058.01 of the week's settled value in this sample. Most of what they removed is one structure, described next.

## One week of Meridian is one ring

Nine wallets form a closed loop on Meridian. Inside the group, 763 payments moved $16,523.21 during the week. Payments in from outside the nine: zero. Payments out: one, $99.00, to 0x30c2282e7e238a977ec710cf67a5d1e1a1bfe85f.

Six of the nine are the wallets ChainWard identified in October, six addresses that have paid only each other since May 2026 and took in $981,397 of delivered volume doing it, by ChainWard's count. In this week's data the six paid each other 415 times, $8,982.28. The other three wallets in the loop were not in ChainWard's set. The remaining 348 payments inside the ring, $7,540.93, involve at least one of the three. The ring also sent its only outside payment to the same exit address ChainWard named.

Put against the facilitator's whole week in the index: Meridian settled 809 payments worth $19,929.16. The ring is 82.9 percent of that value. Strip out everything the three filters flag and Meridian's week is 11 payments worth $2,000.79. Ten of those eleven are the subject of the next section.

## The seller the filters keep

The largest recipient in the adjusted set is 0xc2204317799b521cd1ff1f7c6cab84d3ac5f774e, with $1,901.79 across 10 payments, 33.9 percent of all adjusted value in the sample. Every payment came from one wallet, 0x1cfffac9aa5590338f2650f1461b70feddad0fcb, roughly one a day, sized $72.27 to $247.50.

ChainWard described this same pair a fortnight earlier: a seller working the same Meridian cashback mechanism as the six, with a single payer, returning what it receives. In this week's index data there is no return leg. The return may move as a plain transfer, which this dataset does not contain, and the mechanical filters need a return leg or a cycle to fire. So the filters keep it, and this note names it instead. An adjusted count that hides its own largest miss would be doing the thing it accuses the raw count of doing.

## Wallets paying themselves

815 payments in the sample, 7.1 percent of the count and $421.73 of value, have the same address on both sides. One address, 0xd8429209aee6a398b9707dff5f28aaa93452ee95, paid itself 472 times through PayAI for $108.00 in total. Another, 0xd2670d9ecfb173c7643967fa5460fd936a2204ff, paid itself 97 times at exactly one cent each, $0.97 in total. A payment from a wallet to itself satisfies the seller-funded-buyer test by construction, so the filters remove all 815. They are reported as their own line because a self-payment is a fact about the traffic, not an inference from a graph rule.

A second, smaller closed loop also trips the filters: six wallets, 33 payments among them, $211.44, against five payments in from outside worth $0.09 combined.

## The shape of what is left

Payment sizes in the raw sample: median $0.10. 9,948 payments, 87.0 percent of the count, are at or under ten cents and carry $588.13 between them, 2.4 percent of the value. The largest single payment is $396.00. That size shape, a very large number of very small payments, is also what Chainalysis published for Base in October 2026: over 87 percent of the payments they analyzed sat between $0.0001 and $0.10. On shape, the index and Chainalysis agree. On totals, as the next section shows, nobody agrees with anybody.

After adjustment, PayAI's week is 3,531 payments worth $2,553.69 and Ultravioleta DAO's is 5,267 payments worth $1,058.21. Ultravioleta is where ChainWard, reading full transfer histories rather than an index, found the deepest funding problem: in their 15 September to 5 October sample, 99.2 percent of Ultravioleta settlements went to sellers whose buyers the seller had funded. This cut's funding test sees only funding that itself moved as an indexed payment, so its Ultravioleta adjustment, 16.7 percent of value removed, is a floor under ChainWard's figure, not a contradiction of it.

## What the other counters say

Each of these figures is the named source's own, printed with its scope:

- Chainalysis counts 138.5 million cumulative x402 transactions on Base through Q3 2026 (Chainalysis, October 2026, as reported).
- The x402 project's dashboard shows 75.41 million transactions and $24.24 million of volume in the last 30 days, all chains (x402.org, read 23 October 2026).
- The x402scan index's own aggregate endpoint reports 567,142 payments and $575,249.76 on Base for the last seven days across all facilitators it tracks (x402scan, queried 23 October 2026). Of that, Coinbase CDP accounts for 483,421 payments and $26,849.00. The Coinbase rows were not pulled for this cut and none of its payments are in the dataset or in any filtered figure here.
- ChainWard's six-wallet loop: 35,142 payments and $981,397 delivered from 5 May 2026 to 9 October 2026 (ChainWard).

These numbers cannot be reconciled, and this note does not reconcile them. They count different things: cumulative against weekly, all chains against one, settled transfers against indexed ones. The gap between the dashboard's $24.24 million month and the index's $575,249.76 week, on the same chain family, is the measurement problem in one line. A count that publishes its unit, its window and its rows can at least be argued with.

## What this sample cannot show

- Coinbase CDP at row level. It is the largest facilitator in the index by count, and nothing here says what its traffic contains.
- Any facilitator outside the three pulled, and any payment the index missed. ChainWard found the index holding 3,503 of 3,554 payments in one Meridian sample, so read these counts as complete for the index and close to complete for these facilitators, not as the chain itself.
- Funding that moves as plain transfers. Seller-funded demand is understated everywhere in this note, by construction.
- Solana. This cut is Base only, and says so.
- Whether any surviving payment bought anything real, and who controls any address. The dataset shows money moving. It does not show goods moving, and it does not name people.

## Method in brief

Unit: one indexed x402 payment on Base, amount as delivered to the recipient, verified against on-chain receipts for a random sample of 13 rows, 13 of 13 matching exactly. Filters, applied to the payment graph: closed loops are strongly connected components with at least 20 internal payments, at least $100 internal volume, and outside inflow under 1 percent of internal plus inflow volume (removed 1,268 payments, $16,842.65, gross of overlaps). Seller-funded buyers are payments whose recipient funded the sender inside the window, directly or through one intermediary, through indexed payments (1,704 payments, $17,361.20, gross). Single-day senders are payments from addresses active on one UTC date only (1,102 payments, $2,209.62, gross). Every closed-loop payment also trips the funding test; the union of the three removes 2,626 payments and $19,058.01. Full rules, the address book, the route log and the reproduction commands are in the methodology note published with the dataset.
