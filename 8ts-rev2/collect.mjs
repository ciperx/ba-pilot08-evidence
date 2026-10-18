#!/usr/bin/env node
/**
 * collect.mjs — BasedAgents capability corpus collector (fixed paging).
 *
 * Fixes the bug the reviewer found in revision 1:
 *   /v1/agents/search IGNORES `offset` and takes `page`. Revision 1 passed offset=0..700,
 *   so it read the top-100 agents eight times. This version pages page=1..pagination.total_pages,
 *   with no hard cap, and dedupes by agent_id.
 *   /v1/tasks accepts `offset` (here with status=all so every lifecycle state is included).
 *
 * Also pulls the capability/skill vocabularies of three other public registries, each tagged in
 * observed[].sources with its URL and fetch date.
 *
 * Usage:  node collect.mjs > corpus.json
 * GET only. No writes to any registry, no credentials.
 */

const API = 'https://api.basedagents.ai';
const UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 collect.mjs';
const H = { 'User-Agent': UA, Accept: 'application/json' };
const codes = [];

async function getJSON(url) {
  const res = await fetch(url, { headers: H });
  codes.push(`${res.status} ${url}`);
  if (!res.ok) throw new Error(`${res.status} ${url}`);
  return res.json();
}

// ── 1. every agent: page=1..pagination.total_pages, dedupe by agent_id, no hard cap ──
async function collectAgents() {
  const byId = new Map();
  let page = 1;
  let totalPages = null;
  for (;;) {
    const d = await getJSON(`${API}/v1/agents/search?page=${page}&limit=100`);
    const pg = d.pagination || {};
    if (totalPages === null) totalPages = pg.total_pages ?? 1;
    let fresh = 0;
    for (const a of d.agents || []) {
      if (a.agent_id && !byId.has(a.agent_id)) { byId.set(a.agent_id, a); fresh++; }
    }
    console.error(`agents page ${page}/${totalPages} fresh=${fresh} cumulative=${byId.size}`);
    // stop when we have walked every page AND the API has stopped yielding fresh rows
    if (page >= totalPages && fresh === 0) break;
    if (page > totalPages + 5) break;      // safety valve only; not a corpus cap
    page++;
  }
  return [...byId.values()];
}

// ── 2. every task, including non-open states ──
async function collectTasks() {
  const byId = new Map();
  for (let offset = 0; ; offset += 100) {
    const d = await getJSON(`${API}/v1/tasks?status=all&limit=100&offset=${offset}`);
    const rows = d.tasks || [];
    let fresh = 0;
    for (const t of rows) {
      const id = t.task_id || t.id;
      if (id && !byId.has(id)) { byId.set(id, t); fresh++; }
    }
    console.error(`tasks offset ${offset} fresh=${fresh} cumulative=${byId.size}`);
    if (rows.length < 100 || fresh === 0) break;
  }
  return [...byId.values()];
}

// ── 3. external registries that publish capability/skill vocabularies ──
async function collectExternal() {
  const ext = {};
  const ghDir = async (path) => {
    const d = await getJSON(`https://api.github.com/repos/agntcy/oasf/contents/${path}`);
    return Array.isArray(d) ? d : [];
  };
  // AGNTCY OASF schema: skills + industry domains
  const skillDirs = (await ghDir('schema/skills')).filter(x => x.type === 'dir').map(x => x.name);
  const domainDirs = (await ghDir('schema/domains')).filter(x => x.type === 'dir').map(x => x.name);
  const classes = [];
  for (const cat of skillDirs) {
    for (const e of await ghDir(`schema/skills/${cat}`)) {
      if (e.type === 'dir') {
        for (const y of await ghDir(`schema/skills/${cat}/${e.name}`)) {
          if (y.name.endsWith('.json') && y.name !== 'base_skill.json')
            classes.push({ class: y.name.replace(/\.json$/, ''), category: cat });
        }
      } else if (e.name.endsWith('.json') && e.name !== 'base_skill.json') {
        classes.push({ class: e.name.replace(/\.json$/, ''), category: cat });
      }
    }
  }
  ext.oasf = {
    name: 'AGNTCY Open Agentic Schema Framework (OASF)',
    url: 'https://github.com/agntcy/oasf/tree/main/schema',
    fetched: new Date().toISOString().slice(0, 10),
    skills_top: skillDirs, domains_top: domainDirs, skill_classes: classes,
  };
  // A2A agent cards that publish skills[]
  for (const [key, url] of [
    ['opentask', 'https://opentask.ai/.well-known/agent-card.json'],
    ['payanagent', 'https://payanagent.com/.well-known/agent.json'],
  ]) {
    try {
      const card = await getJSON(url);
      ext[key] = { name: key, url, fetched: new Date().toISOString().slice(0, 10),
                   skills: card.skills || [], capabilities: card.capabilities || {} };
    } catch (e) { ext[key] = { name: key, url, error: String(e) }; }
  }
  // MCP Registry — fetched for completeness but its server names are registry identifiers,
  // not capability strings, so they are NOT added to observed[] (documented in coverage_proof).
  try {
    const d = await getJSON('https://registry.modelcontextprotocol.io/v0/servers?limit=100');
    ext.mcp_registry = { name: 'MCP Registry',
      url: 'https://registry.modelcontextprotocol.io/v0/servers',
      servers: (d.servers || []).map(s => s.server?.name),
      note: 'server names are registry identifiers, not capability strings — excluded from observed[]' };
  } catch (e) { /* optional */ }
  return ext;
}

const [agents, tasks, external] = await Promise.all([collectAgents(), collectTasks(), collectExternal()]);
const as_of = new Date().toISOString().replace(/\.\d+Z$/, 'Z');
const out = { as_of, source_status: { agents_rows: agents.length, tasks_rows: tasks.length }, agents, tasks, external };
console.log(JSON.stringify(out, null, 1));
console.error(codes.join('\n'));
console.error(`DEDUPED agents=${agents.length} tasks=${tasks.length}`);
