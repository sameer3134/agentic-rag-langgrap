---
model: claude-sonnet-4-6
---

Graph-guided multi-agent code review using pre-built graphify knowledge graphs discovered across the repository.

[Extended thinking: This command discovers all graphify-out/graph.json files in any subdirectory, merges their god nodes and cross-layer context, and passes it to parallel review agents. If the argument is a diff/patch file or git diff output, changed files are extracted first — review agents then focus on those files and their graph neighbours, not the whole codebase. This gives reviewers pre-computed blast-radius and architecture context before reading a single line.]

## Step 1 — Parse diff (if provided)

Check whether `$ARGUMENTS` looks like a diff source: a `.diff` or `.patch` file path, a git branch/commit range (e.g. `main..HEAD`), or the word `diff`/`HEAD`/`staged`. If it does, extract the list of changed files now — this list will scope every review agent.

```powershell
python -c "
import sys, json, re, subprocess
from pathlib import Path

arg = '$ARGUMENTS'.strip()
changed_files = []
diff_text = ''

# Case 1: explicit .diff / .patch file
if arg.endswith(('.diff', '.patch')) and Path(arg).exists():
    diff_text = Path(arg).read_text(encoding='utf-8', errors='replace')

# Case 2: git diff range or keyword
elif arg in ('staged', '--staged', '--cached'):
    diff_text = subprocess.run(['git', 'diff', '--staged'], capture_output=True, text=True).stdout
elif re.match(r'^[\w./~^-]+\.\.[\w./~^-]+$', arg) or re.match(r'^[0-9a-f]{6,}$', arg):
    diff_text = subprocess.run(['git', 'diff', arg], capture_output=True, text=True).stdout
elif not arg or arg in ('HEAD', 'diff'):
    diff_text = subprocess.run(['git', 'diff', 'HEAD'], capture_output=True, text=True).stdout

# Extract changed file paths from diff
if diff_text:
    for m in re.finditer(r'^\\+\\+\\+ b/(.+)$', diff_text, re.MULTILINE):
        changed_files.append(m.group(1).strip())
    changed_files = list(dict.fromkeys(changed_files))  # dedup, preserve order
    print(f'DIFF: {len(changed_files)} changed files')
    for f in changed_files:
        print(f'  {f}')
else:
    print('NO_DIFF: reviewing target as directory/path')

Path('.graphify_review_diff.json').write_text(json.dumps({
    'changed_files': changed_files,
    'has_diff': bool(diff_text),
    'diff_text': diff_text[:8000] if diff_text else '',  # first 8k for agent context
}))
"
```

If `changed_files` is non-empty, every review agent below must **prioritize those files and their immediate graph neighbours** — flag issues in changed files as higher severity than background findings.

---

## Step 2 — Discover and load all graphs

Do NOT assume a graph at the root. Search for every `graphify-out/graph.json` under the working directory, load them all, and combine their god nodes and cross-layer edges into unified context.

```powershell
python -c "
import json
from pathlib import Path
from networkx.readwrite import json_graph
import networkx as nx

# Discover all graphs
graph_paths = list(Path('.').rglob('graphify-out/graph.json'))
if not graph_paths:
    print('ERROR: No graphify graphs found in any subdirectory.')
    print('Run: /graphify <service-path>  (e.g. /graphify system-server)')
    raise SystemExit(1)

print(f'Found {len(graph_paths)} graph(s):')
for p in graph_paths:
    print(f'  {p}')

# Load changed files scope (from Step 1)
diff_info = json.loads(Path('.graphify_review_diff.json').read_text()) if Path('.graphify_review_diff.json').exists() else {'changed_files': [], 'has_diff': False}
changed_files = set(diff_info.get('changed_files', []))

all_god_nodes = []
all_cross_layer = []
graph_summaries = []

for graph_path in graph_paths:
    service_name = graph_path.parts[-3] if len(graph_path.parts) >= 3 else str(graph_path)
    try:
        G = json_graph.node_link_graph(json.loads(graph_path.read_text(encoding='utf-8')), edges='links')
    except Exception as e:
        print(f'  WARN: Could not load {graph_path}: {e}')
        continue

    # Scope god nodes to changed files if diff available
    if changed_files:
        # Find nodes that belong to changed files or are neighbours of them
        relevant_nodes = set()
        for nid, d in G.nodes(data=True):
            sf = d.get('source_file', '')
            if any(sf.endswith(cf) or cf.endswith(sf) for cf in changed_files):
                relevant_nodes.add(nid)
        # Add 1-hop neighbours
        neighbours = set()
        for nid in relevant_nodes:
            neighbours.update(G.neighbors(nid))
        scoped_nodes = relevant_nodes | neighbours
        god_pool = [(nid, d) for nid, d in G.nodes(data=True) if nid in scoped_nodes]
        god_pool.sort(key=lambda x: G.degree(x[0]), reverse=True)
        label = f'[DIFF-SCOPED] {service_name}'
    else:
        god_pool = sorted(G.nodes(data=True), key=lambda x: G.degree(x[0]), reverse=True)
        label = service_name

    top_gods = god_pool[:8]
    for nid, d in top_gods:
        all_god_nodes.append({
            'service': service_name,
            'label': d.get('label', nid),
            'degree': G.degree(nid),
            'source_file': d.get('source_file', ''),
            'in_diff': any(d.get('source_file','').endswith(cf) for cf in changed_files),
        })

    # Cross-layer edges
    for u, v, d in G.edges(data=True):
        src = G.nodes[u].get('source_file', '') or ''
        tgt = G.nodes[v].get('source_file', '') or ''
        parts_u = [p for p in src.replace('\\\\', '/').split('/') if p]
        parts_v = [p for p in tgt.replace('\\\\', '/').split('/') if p]
        layer_u = parts_u[2] if len(parts_u) > 2 else ''
        layer_v = parts_v[2] if len(parts_v) > 2 else ''
        if layer_u and layer_v and layer_u != layer_v:
            in_diff = (any(src.endswith(cf) for cf in changed_files) or
                       any(tgt.endswith(cf) for cf in changed_files))
            all_cross_layer.append({
                'service': service_name,
                'from': f'{G.nodes[u].get(\"label\",u)} ({layer_u})',
                'to': f'{G.nodes[v].get(\"label\",v)} ({layer_v})',
                'confidence': d.get('confidence', ''),
                'in_diff': in_diff,
            })

    graph_summaries.append(f'{service_name}: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges')

# Save combined context
ctx = {
    'graph_summaries': graph_summaries,
    'god_nodes': all_god_nodes,
    'cross_layer_edges': all_cross_layer[:40],  # cap at 40 to avoid token bloat
    'changed_files': list(changed_files),
    'has_diff': diff_info.get('has_diff', False),
    'diff_snippet': diff_info.get('diff_text', ''),
}
Path('.graphify_review_ctx.json').write_text(json.dumps(ctx, indent=2))

print()
print('=== COMBINED GRAPH CONTEXT ===')
for s in graph_summaries:
    print(f'  {s}')
print()
print(f'God nodes (top {min(8,len(all_god_nodes))}):')
for g in all_god_nodes[:8]:
    diff_tag = ' [IN DIFF]' if g['in_diff'] else ''
    print(f'  [{g[\"service\"]}] {g[\"label\"]} — degree {g[\"degree\"]} — {g[\"source_file\"]}{diff_tag}')
print()
print(f'Cross-layer edges: {len(all_cross_layer)} total (showing up to 15):')
for e in all_cross_layer[:15]:
    diff_tag = ' [IN DIFF]' if e['in_diff'] else ''
    print(f'  [{e[\"service\"]}] {e[\"from\"]} --> {e[\"to\"]} [{e[\"confidence\"]}]{diff_tag}')
"
```

If the script prints `ERROR: No graphify graphs found`, stop and tell the user which paths to run `/graphify` on first. Do not proceed.

Read `.graphify_review_ctx.json` — this is your graph context. Pass it verbatim to all three agents below.

---

## Step 3 — Dispatch review agents (all three in parallel)

Run all three agents in a **single message** (one Agent tool call each). Pass the graph context and diff info as part of each prompt.

### Agent 1 — Architecture Review

```
You are doing an architecture review.

TARGET: $ARGUMENTS

GRAPH CONTEXT (from knowledge graphs across the repo):
[insert full content of .graphify_review_ctx.json here]

DIFF MODE: [YES if has_diff=true, NO otherwise]
If DIFF MODE is YES:
- The changed_files list is your PRIMARY focus. Flag issues in changed files as CRITICAL or IMPORTANT.
- Use god_nodes and cross_layer_edges to understand blast radius of the changes.
- If a changed file touches a god node, call that out explicitly — high blast radius change.
- Still report architecture violations found outside the diff as MINOR unless they're directly triggered by the diff.

Review focus:
- Layer dependency direction (services should not call api/, infrastructure should not import domain)
- Whether any cross_layer_edges in the diff represent new violations or pre-existing ones
- Service/module boundary violations — any tight coupling introduced by the diff
- God-object anti-patterns — does the diff make any god node even more connected?
- Hardcoded conditionals (if/elif chains) that belong in a registry/dispatcher
- Missing abstractions, duplicate logic, dead code paths

Output:
### Critical — Block Merge
[ARCH-N] Title
File: path:line
Issue and exact fix.

### Important — Fix Before Ship
### Minor — Nice to Fix
### Positive Findings
```

### Agent 2 — Security Review

```
You are doing a security review.

TARGET: $ARGUMENTS

GRAPH CONTEXT (from knowledge graphs across the repo):
[insert full content of .graphify_review_ctx.json here]

DIFF MODE: [YES if has_diff=true, NO otherwise]
If DIFF MODE is YES:
- Focus on changed_files. God nodes that are IN DIFF are highest-priority attack surface.
- Cross-layer edges IN DIFF are candidate auth boundary violations.
- Include the diff_snippet in your analysis — look for new endpoints, removed validation, changed auth logic.

Review focus (OWASP Top-10 2021):
- A01 Broken Access Control: ownership checks, cross-tenant isolation, IDOR in god nodes
- A03 Injection: SQL, path traversal, shell injection via filenames or user-supplied strings
- A04 Insecure Design: missing rate limits, size caps, unbounded inputs, concurrency issues
- A07 Auth Failures: JWT handling, token scope, session management
- A08 Integrity Failures: hash verification, missing input validation on broker/queue messages
- Info disclosure: stack traces in error responses, internal paths leaked

Output:
### Critical [HIGH] — Block Merge
[SEC-N] Title
File: path:line
OWASP category, attack vector, remediation with code snippet.

### Important [MED]
### Minor [LOW]
```

### Agent 3 — Code Quality Review

```
You are doing a code quality review.

TARGET: $ARGUMENTS

GRAPH CONTEXT (from knowledge graphs across the repo):
[insert full content of .graphify_review_ctx.json here]

DIFF MODE: [YES if has_diff=true, NO otherwise]
If DIFF MODE is YES:
- Read the diff_snippet first. Focus correctness and quality issues on changed_files.
- Use god_nodes to identify if changed code is in a high-blast-radius location — if so, correctness issues there are automatically CRITICAL.
- Nodes with many INFERRED edges touched by the diff may have implicit coupling the author missed.

Review focus:
- Functional correctness: are new functions wired up correctly end-to-end?
- Schema contract compliance: do serializer outputs match declared Pydantic/Zod schemas?
- Duplicate logic introduced by the diff vs. existing helpers
- Broad exception handling (bare except, catch-all without re-raise)
- Tests that cannot fail (assertions missing, try/except pass)
- Silent fallbacks that hide bugs vs. explicit fail-fast
- Type consistency across the call stack
- Method size and single-responsibility principle

Output:
### Critical — Correctness Blockers
[CQ-N] Title
File: path:line
Issue, impact, and fix.

### Important — Quality Debt
### Minor — Style/Nit
### Positive Findings
```

---

## Step 4 — Consolidate

After all three agents return, deduplicate (same file:line + same root cause = one entry) and produce:

```markdown
# Graph-Guided Code Review — $ARGUMENTS

## Review Scope
- Mode: [DIFF-SCOPED | FULL CODEBASE]
- Changed files reviewed: N  (if diff mode)
- Graphs used: [list service names]
- Graph stats: [node/edge counts per service]
- God nodes in diff: [list if any]

---

## Critical — Block Merge
[Merged, deduplicated, ranked by blast radius — god-node issues first]

## Important — Fix Before Ship

## Minor — Nice to Fix

## Positive Findings

---

## Deduplication Log
[Issues flagged by multiple agents — note which ones]

## Summary Table
| Category     | Critical | Important | Minor |
|--------------|----------|-----------|-------|
| Architecture |    N     |     N     |   N   |
| Security     |    N     |     N     |   N   |
| Code Quality |    N     |     N     |   N   |

Do not merge until all Critical items are resolved.
```

**Deduplication rule**: same file:line + same root cause → keep the more detailed finding, note "also flagged by [agent]".

**Blast-radius ranking rule**: issues in god nodes or nodes with cross-layer edges rank above same-severity issues elsewhere.

---

## Cleanup

```powershell
Remove-Item -ErrorAction SilentlyContinue .graphify_review_diff.json, .graphify_review_ctx.json
```
