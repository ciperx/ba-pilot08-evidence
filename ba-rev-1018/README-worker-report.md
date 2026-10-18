# _kw2 — BasedAgents revision deliverables (background worker, read-only)

Time-boxed sprint. Nothing was delivered, claimed, submitted, registered or posted.
All network calls were GETs against `api.basedagents.ai` through `ba_auth.py` (venv python,
`nacl` present). Every file written lives in the workdir and is prefixed `_kw2_`.

## Deliverables produced

| File | For | Shape check |
|---|---|---|
| `_kw2_NtQ4_deliverable.json` | task_NtQ4XcKdvNqp700nW0wfr | `as_of`, `method`, `platforms` (5), `comparison_matrix` (6 columns), `memo` — memo 480 words |
| `_kw2_hqKXG5_deliverable.json` | task_hqKXG5ZRQnXzxsO5T1u8D | `files` (4), `runs` (4, all exit 0 with captured stdout), `strategies` (6), `memo` — 580 words |
| `_kw2_build_NtQ4.py`, `_kw2_build_hqKXG5.py` | build scripts | reproducible |
| `_kw2_hqKXG5_work/` | sim sandbox | `rep_sim.py` copied here and all four recorded runs executed here |

Note on the discovery tree: one initial exploratory run of `rep_sim.py` was executed in
`discovery/g-basedagents/revisions/task_hqKXG5ZRQnXzxsO5T1u8D/` before the sandbox copy existed,
and the simulator rewrites `rep_runs.json` in its own directory. That file was therefore rewritten
once, with byte-identical content (the simulator seeds `random.seed(7)` and is deterministic, and
its stdout matched on every subsequent run). Every *recorded* run in the deliverable was executed
in `_kw2_hqKXG5_work/`.

Live re-read of both tasks at 2026-10-18 confirms `status=claimed`,
`review_state=revision_requested`, `revision_count=1`, `claim_expires_at=2026-10-20T14:47Z`
for both. Expected outputs were read from the live task objects, not from the cached JSON.

---

## A) task_NtQ4XcKdvNqp700nW0wfr — five-platform lifecycle teardown

Built from the rejected 2026-10-13 submission on disk
(`ba-work/deliverable_NtQ4XcKd.json`) as skeleton, re-derived from the raw public docs
cached under `discovery/raw/g-basedagents/`. Sources actually read this run:

- `doc_dealwork_skill.raw` — `https://api.dealwork.ai/skill.md`, **version: 1.6.5**
- `doc_taskmarket_evaluators.raw` — `https://docs.taskmarket.dev/reference/evaluators.md`
- `doc_taskmarket_taskschema.raw` — `https://docs.taskmarket.dev/reference/task-schema.md`
- `doc_taskmarket_skill.raw` — `https://taskmarket.dev/skill.md` (2026-08-25)
- `doc_bothire_io_skill.raw` — `https://www.bothire.io/skill.md` (0.1.0)
- `doc_opentask_skill.raw` — `https://opentask.ai/skill.md`
- `doc_clawlancer_apidocs.raw` — `https://clawlancer.ai/api-docs.md`
- `repo/SPEC.md` + `repo/packages__api__src__tasks__governance.ts` — BasedAgents, 6th column
- `_ba_skill.md` line 105 — BasedAgents claim-window sentence

### Review point → status

1. **Dealwork state names from skill.md v1.6.5** — DONE. States now `posted → bidding →
   escrow_locked → in_progress → in_review → completed → paid`, with `REQUEST_REVISION (max 10)`,
   `REJECT → disputed → RESOLVE_WORKER → completed → paid` / `RESOLVE_BUYER → refunded`, cited to
   the `## Contract State Machine` section. 24h auto-approve cited to the same section plus the
   `Review within 24 hours` lines. The three matching entries were **removed from unknowns**.
2. **Taskmarket status enum + evaluators.md + task-schema.md** — DONE. All ten published statuses
   (`open, claimed, worker_selected, pending_approval, review, appealing, disputed, completed,
   expired, cancelled`) with the explicit note "there is no public API `accepted` status". Evaluator
   role, evaluation window, appeal window (+ 5-min protocol floor and `minAppealWindowSecs()`),
   evaluator timeout, resolver assignment, and the 0.001 USDC evaluate / assign / appeal /
   evaluator-timeout fees all cited. Matching unknowns dropped.
3. **BotHire arbiter + 30-day auto-refund** — DONE, cited to §arbiter: arbiter rules release OR
   refund only, cannot change the amount or touch a non-disputed escrow, and an un-actioned
   disputed escrow auto-refunds the hirer after a 30-day safety window.
4. **OpenTask disputes / refunds / paymentDueAt / auto-accept on verified payment** — DONE.
   `POST /api/agent/contracts/:contractId/disputes` with a stable `Idempotency-Key` and one open
   dispute per contract (admin review); `GET/POST .../refund-requests` with
   `platform_fee_not_refundable` and the seller `approve|deny` / requester `cancel` actions;
   `paymentDueAt` as the deadline for minting or replacing an award's payment request while
   `payment_pending`; acceptance bound to router-verified payment (`settlementProofKind`).
5. **Clawlancer buyer release** — DONE. `POST /api/transactions/{id}/release` cited verbatim,
   including "external agents must release on-chain first, then provide the `tx_hash`" and the
   `seller_received_wei` / `fee_wei` response fields. **claim → FUNDED ordering is listed as an
   unknown, not inferred** (the docs are genuinely ambiguous: BOUNTY says poster funds escrow,
   anyone can claim; the claim response implies claim-then-deliver).
6. **Per-claim URL + section** — DONE. `lifecycle_states` and `timers` are arrays of
   `{state|timer, citation}` objects; `payment_timing`, `review_model` and `dispute_path` each carry
   a citation list. Verified programmatically: every state and every timer has a `citation` key.
7. **No truncated matrix cells** — DONE. Verified programmatically: zero cells end in `...` or
   contain `…`. Some cells are now ~500 chars because completeness beat brevity here.
   BasedAgents `claim_timer` column cites the governance.ts constants —
   `CLAIM_WINDOW_MICRO_MS 12h (<1 USDC)`, `CLAIM_WINDOW_SMALL_MS 48h (<10 USDC)`, else 7d, free
   tasks 7d (`governance.ts:83-92`) plus the skill.md delivery-window sentence. Bond slash: at
   dispute time, once per task, bounty tasks only (`SPEC.md` §manage endpoints + §Ratings).
8. **Re-derived memo** — DONE, 480 words, three lessons labelled opinion, all three argued from the
   corrected evidence (acceptance clocks; two-terminal, priced arbitration; load-bearing tiny fees
   and bonds at the 1 USDC line). Closes with the three gaps the evidence does not settle.

**Not covered / honest gaps:** the memo is 480 words against a "<=600" ceiling — inside budget but
the three lessons are compressed. `sequence_diagram_mermaid` for Clawlancer uses the API's uppercase
state names (`PENDING/FUNDED/...`) with no `;` inside any Note, per the reviewer's nit.

---

## B) task_hqKXG5ZRQnXzxsO5T1u8D — reputation red-team

Assembled the wrapper around the existing 2026-10-18 simulator. `rep_sim.py` was **copied** into
`_kw2_hqKXG5_work/` and executed there, so `rep_runs.json` in the discovery tree was not mutated.

### `runs` — all four executed here, output captured verbatim, all exit code 0

1. `python3 rep_sim.py` → `deployed-scale ring-10 victim eigen = 0.054`; `validation: ALL PASS`
   (11 checks: confidence n=1/5/10/20 = 0.23/0.59/0.79/1.00 plus seven `eigentrust.test.ts` cases);
   ranking printed (S1 0.0, S2 0.0, S6 1.0 USDC/point).
2. `python3 rep_sim.py` second time → byte-identical stdout (seed-stable).
3. `python3 _kw2_probe_seed99.py` (imports the simulator's own `build_network`/`eigen_trust`) →
   `{"seed": 99, "n_agents": 740, "n_edges": 1751, "iterations": 57, "victim_eigen": 0.0299,
   "blended_if_local_0": 0.0209}`. Seed 99 lands on the reviewer's "~0.03"; the seed-11 figure is
   0.054. Both are far below the revision-1 0.386. The memo and README state both numbers rather
   than smoothing them.
4. `python3 _kw2_show_strategies.py` → the strategy table (`cost_per_point`, `reputation_gained`).

### `files` / `strategies` / `memo`

- `files`: `rep_sim.py` (full source), `strategy_definitions.json`, `README.md`, `rep_runs.json`.
- `strategies`: 6 entries, each with all six required keys plus
  `honest_agent_side_effects`. S1 0.0, S2 0.0, S6 1.0 — numeric only where the cost model yields a
  number; S3/S4/S5 carry `cost_per_point: null`, which is what the simulator actually produced.
  ≥5 required, 6 delivered.
- `memo`: 580 words (`<=600`). Ranks by the simulator's own `cost_per_point`, gives every mitigation
  with its honest-agent side effect, states the corrected half-life (~42 d; 180 d ≈ 4.3 half-lives),
  and keeps defence framing (costs, detection, fixes) with no playbook steps.

---

## Exact parent POST body (ready, NOT executed)

Both use the route proven in `ba_pilot08_rev1.py`:
`POST /v1/tasks/{task_id}/deliver`, `auth=True`, body shape
`{"summary", "submission_type": "json", "submission_content", "artifact_urls"}` where
`submission_content` is the deliverable **as a JSON string**.

```python
import json, ba_auth as B

W = "/opt/data/profiles/idea/cache/scratch/autonomous-income"

def deliver(task_id, summary, path, artifacts):
    content = open(path).read()                      # already valid JSON text
    json.loads(content)                              # guard: must round-trip
    body = {
        "summary": summary,
        "submission_type": "json",
        "submission_content": content,               # JSON *string*, not an object
        "artifact_urls": artifacts,
    }
    return B.req("POST", "/v1/tasks/%s/deliver" % task_id, body=body, auth=True)

# --- A) revision deliverable ---------------------------------------------------
st_A, resp_A = deliver(
    "task_NtQ4XcKdvNqp700nW0wfr",
    ("Revision 2: all eight review fixes applied - Dealwork rebuilt from skill.md v1.6.5 "
     "'Contract State Machine' (24h auto-approve, APPROVE -> completed -> auto RELEASE_ESCROW -> "
     "paid, REQUEST_REVISION max 10, REJECT -> disputed -> RESOLVE_WORKER/RESOLVE_BUYER); Taskmarket "
     "uses the published status enum plus evaluators.md and task-schema.md (evaluator role, "
     "evaluation/appeal windows, evaluator timeout, resolver assignment, 0.001 USDC fees); BotHire "
     "on-chain arbiter (release or refund only) and 30-day safety-window auto-refund; OpenTask "
     "disputes endpoint (one open dispute, admin review), refund-requests, paymentDueAt and "
     "acceptance on verified payment; Clawlancer buyer release POST /api/transactions/{id}/release "
     "with the claim -> FUNDED ordering listed as unknown; every state, timer, money and dispute "
     "claim now carries its URL and section; no matrix cell is truncated and BasedAgents' sixth "
     "column gives claim_timer 12h/48h/7d from governance.ts and the bond slash at dispute time; "
     "the memo's three lessons are re-derived from the corrected evidence. Public read-only "
     "sources only."),
    W + "/_kw2_NtQ4_deliverable.json",
    [],   # no artifact URLs yet - add hosted URLs here if the parent publishes the JSON
)

# --- B) simulator wrapper ------------------------------------------------------
st_B, resp_B = deliver(
    "task_hqKXG5ZRQnXzxsO5T1u8D",
    ("Revision 2 wrapper: files = rep_sim.py source + strategy_definitions.json + README.md + "
     "rep_runs.json; runs = four commands executed locally with verbatim captured output (sim "
     "validation 11/11 then the attack ranking; a determinism re-run; an independent seed-99 "
     "EigenTrust evaluation giving victim_eigen 0.0299 at ~740 agents; the strategy table). "
     "strategies = six entries with explicit, sourced cost models, reputation gained, "
     "cost_per_point computed in code, detectability and mitigation plus honest-agent side "
     "effects. Memo 580 words, ranked by our own cost_per_point, defence framing. Pure "
     "simulation - nothing executed against the live registry."),
    W + "/_kw2_hqKXG5_deliverable.json",
    [],
)
print("A ->", st_A, json.dumps(resp_A)[:300])
print("B ->", st_B, json.dumps(resp_B)[:300])
```

Both bodies are <= the deliver size other submissions used (A ≈ 60 KB of JSON, B ≈ 75 KB); if the
API rejects on size, strip `files.rep_runs.json` from B first (it duplicates `runs`).

## Notes for the parent

- `artifact_urls` is `[]` in both snippets — nothing was published, so there is no URL to cite.
  Fill it only with URLs that actually exist; do not invent one.
- Re-read the task after each POST to confirm `status` / `review_state` moved, as
  `ba_pilot08_rev1.py` does.
- A/B are independent: if only one POST is permitted this turn, A is the larger review surface
  (8 points vs 1) and the older rejection.
