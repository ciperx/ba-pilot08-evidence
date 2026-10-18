#!/usr/bin/env python3
"""
coverage_check.py — machine-checkable coverage assertion for the capability taxonomy.

Exits 0 only if:
  1. every entry of deliverable.observed[] has a disposition of 'mapped', 'rejected' or 'domain',
  2. the set of capability_string values equals the union of
        {t.maps_from for t in taxonomy.terms}  ∪  {r.capability_string for r in taxonomy.rejected}
        ∪ {d.capability_string for d in taxonomy.domain_axis_from_external_registry}
     exactly — no string in two dispositions' totals that would double count, and nothing missing,
  3. no map target is a term id that does not exist in taxonomy.terms,
  4. the counts in coverage_proof equal the recomputed counts.

Run:  .venv/bin/python coverage_check.py
"""
import json, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(BASE, "deliverable.json")))

observed = d["observed"]
terms = d["taxonomy"]["terms"]
rejected = d["taxonomy"]["rejected"]
domain_axis = d["taxonomy"]["domain_axis_from_external_registry"]
proof = d["coverage_proof"]

errors = []

obs_strings = [row["capability_string"] for row in observed]
obs_set = set(obs_strings)
if len(obs_strings) != len(obs_set):
    errors.append("observed[] contains duplicate capability_string values")

mapped = set()
for t in terms:
    for s in t["maps_from"]:
        if s in mapped:
            errors.append(f"string mapped twice across terms: {s!r}")
        mapped.add(s)

rej = {r["capability_string"] for r in rejected}
dom = {r["capability_string"] for r in domain_axis}

# 1. every observed string has exactly one disposition
unaccounted = obs_set - (mapped | rej | dom)
if unaccounted:
    errors.append(f"{len(unaccounted)} observed strings have no disposition: {sorted(unaccounted)[:10]}")

# 2. nothing is claimed that was not observed
extra = (mapped | rej | dom) - obs_set
if extra:
    errors.append(f"{len(extra)} dispositioned strings were never observed: {sorted(extra)[:10]}")

# 3. every map target exists as a term id
term_ids = {t["id"] for t in terms}
for row in observed:
    if row["disposition"] == "mapped" and row["maps_to"] not in term_ids:
        errors.append(f"dangling map target {row['maps_to']!r} for {row['capability_string']!r}")

# 4. coverage_proof agrees with the recomputation
recount = {"observed_strings": len(obs_set), "mapped": len(mapped),
           "rejected": len(rej), "domain_axis_mapped": len(dom), "unclassified": 0}
for k, v in recount.items():
    if proof.get(k) != v:
        errors.append(f"coverage_proof.{k}={proof.get(k)} but recomputed {v}")

# 5. the union identity holds arithmetically
if len(obs_set) != len(mapped) + len(rej) + len(dom):
    errors.append("|observed| != |mapped| + |rejected| + |domain_axis|")

print(f"observed strings      : {len(obs_set)}")
print(f"mapped                : {len(mapped)}")
print(f"rejected              : {len(rej)}")
print(f"domain-axis mapped    : {len(dom)}")
print(f"terms                 : {len(terms)}  (tier-2)")
print(f"domains               : {len(d['taxonomy']['domains'])}  (tier-1)")
print(f"mapped + rejected + dom = {len(mapped) + len(rej) + len(dom)}")
print()
if errors:
    print("FAIL")
    for e in errors:
        print("  -", e)
    sys.exit(1)
print("PASS  mapped \u222a rejected \u222a domain_axis == observed, and every map target is a real term")
sys.exit(0)
