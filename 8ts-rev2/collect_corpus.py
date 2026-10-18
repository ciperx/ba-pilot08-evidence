#!/usr/bin/env python3
"""
collect_corpus.py — Task task_8tsVQ5tpc7AykJ4Hrbj7l, fixed paging.

Fixes the reviewed paging bug:
  * /v1/agents/search takes `page=` (it IGNORES `offset=`) -> page 1..pagination.total_pages,
    no hard cap, dedupe by agent_id.
  * /v1/tasks accepts `offset=` (or status=all) -> offset-page the whole set.

Writes corpus.json with the deduplicated rows + the external registry vocabularies.
GET only — no writes to any registry.
"""
import json, ssl, os, sys, urllib.request, urllib.error, time

R = "/opt/data/profiles/idea/cache/scratch/autonomous-income/discovery/raw/g-basedagents"
os.makedirs(R, exist_ok=True)
API = "https://api.basedagents.ai"
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
H = {"User-Agent": UA, "Accept": "application/json"}
CODES = []


def get(url, hdrs=None):
    hh = dict(H)
    if hdrs:
        hh.update(hdrs)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=hh), context=ctx, timeout=45) as r:
                CODES.append((url, r.status))
                return r.status, r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            CODES.append((url, e.code))
            try:
                return e.code, e.read().decode("utf-8", "replace")
            except Exception:
                return e.code, ""
        except Exception as e:
            if attempt == 2:
                CODES.append((url, -1))
                return -1, str(e)[:200]
            time.sleep(1.5)


# ─────────────────────────────── BasedAgents agents ───────────────────────────────
agents, seen = [], set()
page, total_pages = 1, None
while True:
    st, body = get(f"{API}/v1/agents/search?page={page}&limit=100")
    if st != 200:
        print("agents page", page, "->", st, body[:160]); break
    d = json.loads(body)
    pg = d.get("pagination") or {}
    if total_pages is None:
        total_pages = pg.get("total_pages")
        print(f"agents: total={pg.get('total')} total_pages={total_pages}")
    rows = d.get("agents", [])
    fresh = 0
    for a in rows:
        aid = a.get("agent_id")
        if aid and aid not in seen:
            seen.add(aid); agents.append(a); fresh += 1
    print(f"  page {page}/{total_pages}: rows={len(rows)} fresh={fresh} cumulative={len(agents)}")
    if not rows or (total_pages and page >= total_pages):
        break
    page += 1

# extra safety: keep paging until the API stops returning fresh rows
while total_pages and page <= total_pages + 5:
    st, body = get(f"{API}/v1/agents/search?page={page}&limit=100")
    if st != 200:
        break
    rows = json.loads(body).get("agents", [])
    fresh = 0
    for a in rows:
        aid = a.get("agent_id")
        if aid and aid not in seen:
            seen.add(aid); agents.append(a); fresh += 1
    if fresh == 0:
        break
    page += 1

# ─────────────────────────────── BasedAgents tasks ───────────────────────────────
tasks, tseen = [], set()
off = 0
while True:
    st, body = get(f"{API}/v1/tasks?status=all&limit=100&offset={off}")
    if st != 200:
        print("tasks offset", off, "->", st, body[:160]); break
    rows = json.loads(body).get("tasks", [])
    fresh = 0
    for t in rows:
        tid = t.get("task_id") or t.get("id")
        if tid and tid not in tseen:
            tseen.add(tid); tasks.append(t); fresh += 1
    print(f"  tasks offset {off}: rows={len(rows)} fresh={fresh} cumulative={len(tasks)}")
    if len(rows) < 100:
        break
    off += 100

# ─────────────────────────── external registry vocabularies ───────────────────────────
ext = {}


def gh_schema_dir(path):
    st, body = get(f"https://api.github.com/repos/agntcy/oasf/contents/{path}")
    if st != 200:
        return st, []
    return st, [x for x in json.loads(body)]


# `schema/skills` is a list of CATEGORY DIRECTORIES plus base_skill.json — walk the dirs.
osfs_skills, osfs_domains = [], []
st_s, items_s = gh_schema_dir("schema/skills")
if st_s == 200:
    osfs_skills = [x["name"] for x in items_s if x["type"] == "dir"]
st_d, items_d = gh_schema_dir("schema/domains")
if st_d == 200:
    osfs_domains = [x["name"] for x in items_d if x["type"] == "dir"]

# one level into each skill category -> the concrete skill classes
oasf_classes = []
for cat in osfs_skills:
    st, items = gh_schema_dir(f"schema/skills/{cat}")
    if st == 200:
        for x in items:
            if x["type"] == "dir":
                st2, items2 = gh_schema_dir(f"schema/skills/{cat}/{x['name']}")
                if st2 == 200:
                    oasf_classes += [y["name"].replace(".json", "") for y in items2 if y["name"].endswith(".json")]
            elif x["name"].endswith(".json") and x["name"] != "base_skill.json":
                oasf_classes.append(x["name"].replace(".json", ""))
    print(f"  oasf skill cat {cat}: running total {len(oasf_classes)}")

ext["oasf"] = {
    "name": "AGNTCY Open Agentic Schema Framework (OASF)",
    "url": "https://github.com/agntcy/oasf/tree/main/schema",
    "fetched": time.strftime("%Y-%m-%d", time.gmtime()),
    "skills_top": osfs_skills,
    "domains_top": osfs_domains,
    "skill_classes": sorted(set(oasf_classes)),
}

# OpenTask A2A agent card
st, body = get("https://opentask.ai/.well-known/agent-card.json")
ext["opentask"] = {"name": "OpenTask", "url": "https://opentask.ai/.well-known/agent-card.json",
                   "fetched": time.strftime("%Y-%m-%d", time.gmtime()), "status": st, "skills": [], "capabilities": {}}
if st == 200:
    card = json.loads(body)
    ext["opentask"]["skills"] = card.get("skills", [])
    ext["opentask"]["capabilities"] = card.get("capabilities", {})

# PayanAgent agent card
st, body = get("https://payanagent.com/.well-known/agent.json")
ext["payanagent"] = {"name": "PayanAgent", "url": "https://payanagent.com/.well-known/agent.json",
                     "fetched": time.strftime("%Y-%m-%d", time.gmtime()), "status": st, "skills": [],
                     "capabilities": {}}
if st == 200:
    try:
        card = json.loads(body)
        ext["payanagent"]["skills"] = card.get("skills", [])
        ext["payanagent"]["capabilities"] = card.get("capabilities", {})
        ext["payanagent"]["raw_keys"] = sorted(card.keys())
    except Exception as e:
        ext["payanagent"]["err"] = str(e)[:120]

# MCP registry (tool-level capability names)
st, body = get("https://registry.modelcontextprotocol.io/v0/servers?limit=100")
ext["mcp_registry"] = {"name": "MCP Registry", "url": "https://registry.modelcontextprotocol.io/v0/servers",
                       "fetched": time.strftime("%Y-%m-%d", time.gmtime()), "status": st, "servers": []}
if st == 200:
    try:
        ext["mcp_registry"]["servers"] = [s["server"]["name"] for s in json.loads(body).get("servers", [])]
    except Exception as e:
        ext["mcp_registry"]["err"] = str(e)[:120]

corpus = {
    "as_of": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "source_status": {"agents_total_pages": total_pages, "agents_rows": len(agents), "tasks_rows": len(tasks)},
    "agents": agents,
    "tasks": tasks,
    "external": ext,
}
json.dump(corpus, open(os.path.join(R, "corpus.json"), "w"), indent=1)
json.dump(CODES, open(os.path.join(R, "collector_codes.json"), "w"), indent=1)
print(f"\nDEDUPED: agents={len(agents)} tasks={len(tasks)}")
print("external:", {k: (v.get("status"), len(v.get("skills") or v.get("servers") or v.get("skill_classes") or [])) for k, v in ext.items()})
