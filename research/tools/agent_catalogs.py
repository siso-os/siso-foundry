#!/usr/bin/env python3
"""Snapshot the public agent-skill, plugin and MCP-server catalogues, and record their most-used entries.

  python3 research/tools/agent_catalogs.py [--only cpd-skills,cpd-plugins,mcp,skillsmp] [--min-installs 1000]

Sources (all public JSON APIs, no login):
  cpd-skills   claude-plugins.dev/api/skills      Claude Code / agent skills with stars and installs
  cpd-plugins  claude-plugins.dev/api/plugins     Claude Code plugins with stars and downloads
  mcp          registry.modelcontextprotocol.io   the official MCP server registry
  skillsmp     skillsmp.com/api/skills            SkillsMP's top skills by stars (the API caps at 1,200)

Full snapshots are data: they go to the data plane as foundry-data/research/agent-bases/<source>-<date>.jsonl, which
`foundry find --domain agent-bases` searches. Git gets records only for heavily used entries, rewritten each run as
research/agent-bases/observations/agent-catalogs.jsonl (skills with --min-installs or more).
"""
import argparse, concurrent.futures as cf, json, os, sys, time, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UA = "siso-foundry-research"


def get(url):
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            return json.loads(urllib.request.urlopen(req, timeout=60).read())
        except Exception as e:
            if attempt == 3:
                print(f"  failed {url}: {e}", file=sys.stderr)
                return None
            time.sleep(2 * (attempt + 1))


def offset_pages(base, key, total, per=100, workers=4):
    urls = [f"{base}{'&' if '?' in base else '?'}limit={per}&offset={o}" for o in range(0, total, per)]
    out = []
    with cf.ThreadPoolExecutor(workers) as pool:
        for d in pool.map(get, urls):
            out += (d or {}).get(key) or []
    return out


def cpd(kind):
    base = f"https://claude-plugins.dev/api/{kind}"
    total = get(f"{base}?limit=1")["total"]
    rows = offset_pages(base, kind, total)
    return {r["id"]: r for r in rows}.values()  # pages can overlap while the catalogue changes


def mcp():
    rows, cursor = [], None
    while True:
        d = get("https://registry.modelcontextprotocol.io/v0/servers?limit=100" + (f"&cursor={urllib.parse.quote(cursor)}" if cursor else ""))
        if not d:
            break
        rows += d.get("servers") or []
        cursor = (d.get("metadata") or {}).get("nextCursor")
        if not cursor:
            break
    latest = {}
    for s in rows:  # one row per server name, newest version
        srv = s.get("server") or {}
        latest[srv.get("name")] = s
    return latest.values()


def skillsmp():
    rows = []
    for page in range(1, 61):  # the API rejects pages larger than 20
        d = get(f"https://skillsmp.com/api/skills?limit=20&page={page}&sortBy=stars")
        rows += (d or {}).get("skills") or []
        if not d or not d.get("pagination", {}).get("hasNext"):
            break
    return {r["id"]: r for r in rows}.values()


def records(name, rows, min_installs):
    """Heavily used skills become records (plugins have no page of their own; they stay searchable in the snapshot)."""
    for r in rows:
        if name == "cpd-skills" and (r.get("installs") or 0) >= min_installs:
            # the skill's own page: its GitHub tree URL would key every skill of a repo to one record
            yield {"url": f"https://claude-plugins.dev/skills/{r['namespace']}", "title": r["name"], "kind": "skill", "area": "skill-hubs",
                   "why": f"{(r.get('description') or '').strip()[:200]} ({r['installs']:,} installs on claude-plugins.dev; source {r.get('sourceUrl') or 'n/a'})",
                   "by": r.get("author") or "", "stars": r.get("stars"), "tags": ["claude-plugins.dev", "skill"],
                   "source": "https://claude-plugins.dev/api/skills"}


def item(name, r):
    """One find-ready row per catalogue entry (the slim form `foundry find` reads)."""
    if name == "cpd-skills":
        return {"id": f"cpd-skill:{r['id']}", "title": r.get("name"), "kind": "skill", "area": "catalog-skill",
                "url": f"https://claude-plugins.dev/skills/{r.get('namespace', '')}", "why": r.get("description") or "",
                "by": r.get("author") or "", "stars": r.get("stars"), "installs": r.get("installs") or 0, "tags": ["claude-plugins.dev"]}
    if name == "cpd-plugins":
        return {"id": f"cpd-plugin:{r['id']}", "title": r.get("name"), "kind": "plugin", "area": "catalog-plugin",
                "url": r.get("gitUrl") or "", "why": r.get("description") or "", "by": r.get("author") or "", "stars": r.get("stars"),
                "installs": r.get("downloads") or 0, "tags": ["claude-plugins.dev"], "category": r.get("category") or ""}
    if name == "mcp":
        srv = r.get("server") or {}
        url = (srv.get("repository") or {}).get("url") or srv.get("websiteUrl") or next((x.get("url") for x in srv.get("remotes") or []), "")
        return {"id": f"mcp:{srv.get('name')}", "title": srv.get("title") or srv.get("name"), "kind": "mcp-server", "area": "catalog-mcp",
                "url": url or "https://registry.modelcontextprotocol.io", "why": srv.get("description") or "", "by": (srv.get("name") or "").split("/")[0],
                "stars": None, "installs": 0, "tags": ["mcp-registry"]}
    if name == "skillsmp":
        return {"id": f"skillsmp:{r['id']}", "title": r.get("name"), "kind": "skill", "area": "catalog-skill", "url": r.get("githubUrl") or "",
                "why": r.get("description") or "", "by": r.get("author") or "", "stars": r.get("stars"), "installs": 0, "tags": ["skillsmp"]}


def write_items(data):
    """Merge the newest snapshot of each source into agent-catalog-items-<date>.jsonl."""
    out = data / f"agent-catalog-items-{time.strftime('%Y-%m-%d')}.jsonl"
    n = 0
    with open(out, "w", encoding="utf-8") as fh:
        for name in ("cpd-skills", "cpd-plugins", "mcp", "skillsmp"):
            snaps = sorted(data.glob(f"{name}-20*.jsonl"))
            if not snaps:
                continue
            for line in snaps[-1].read_text().split("\n"):
                if line.strip():
                    it = item(name, json.loads(line))
                    if it and it["url"]:
                        fh.write(json.dumps(it, ensure_ascii=False) + "\n")
                        n += 1
    print(f"{n} catalogue items -> {out}", file=sys.stderr)


def write_records(data, min_installs):
    snaps = sorted(data.glob("cpd-skills-20*.jsonl"))
    if not snaps:
        return
    rows = [json.loads(l) for l in snaps[-1].read_text().split("\n") if l.strip()]
    out = ROOT / "research" / "agent-bases" / "observations" / "agent-catalogs.jsonl"
    n = 0
    with open(out, "w", encoding="utf-8") as fh:
        for r in records("cpd-skills", rows, min_installs):
            fh.write(json.dumps({**r, "licence": "see source", "preview": "", "github": "", "free": True,
                                 "date": time.strftime("%Y-%m-%d")}, ensure_ascii=False) + "\n")
            n += 1
    print(f"{n} skills with {min_installs}+ installs -> {out.relative_to(ROOT)}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--only", default="cpd-skills,cpd-plugins,mcp,skillsmp")
    p.add_argument("--min-installs", type=int, default=200)
    p.add_argument("--items-only", action="store_true", help="rebuild the find index from existing snapshots")
    a = p.parse_args()
    data = Path(os.environ.get("FOUNDRY_DATA", "/Volumes/SISO-STORAGE-VAULT/foundry-data")).expanduser() / "research" / "agent-bases"
    data.mkdir(parents=True, exist_ok=True)
    if a.items_only:
        write_items(data)
        return write_records(data, a.min_installs)
    fetch = {"cpd-skills": lambda: cpd("skills"), "cpd-plugins": lambda: cpd("plugins"), "mcp": mcp, "skillsmp": skillsmp}
    for name in a.only.split(","):
        rows = list(fetch[name]())
        snap = data / f"{name}-{time.strftime('%Y-%m-%d')}.jsonl"
        with open(snap, "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"{name}: {len(rows)} entries -> {snap}", file=sys.stderr)
    write_items(data)
    write_records(data, a.min_installs)

if __name__ == "__main__":
    main()
