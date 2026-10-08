#!/usr/bin/env python3
"""Record GitHub repositories for a domain area straight from GitHub's search API (no helper's memory involved).

  python3 research/tools/gh_search.py --domain ui --area shells --min-stars 1000 "shadcn admin dashboard" "nextjs saas starter"

Each query runs through `gh search repos` sorted by stars, skipping archived repos. Appends to
research/<domain>/observations/gh-search.jsonl, skipping repos already there.
"""
import argparse, json, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIELDS = "fullName,description,stargazersCount,license,pushedAt,isArchived,url,homepage"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--domain", required=True)
    p.add_argument("--area", required=True)
    p.add_argument("--min-stars", type=int, default=500)
    p.add_argument("--per", type=int, default=30)
    p.add_argument("--pushed-since", default="2025-01-01", help="skip repos untouched since this date")
    p.add_argument("queries", nargs="+")
    a = p.parse_args()
    out = ROOT / "research" / a.domain / "observations" / "gh-search.jsonl"
    seen = {json.loads(l)["github"].lower() for l in out.read_text().split("\n") if l.strip()} if out.exists() else set()
    added = 0
    with open(out, "a", encoding="utf-8") as fh:
        for q in a.queries:
            res = subprocess.run(["gh", "search", "repos", *q.split(), "--sort", "stars", "--limit", str(a.per),
                                  "--stars", f">={a.min_stars}", "--json", FIELDS], capture_output=True, text=True)
            if res.returncode:
                print(f"search failed: {q}: {res.stderr.strip()[-200:]}", file=sys.stderr)
                continue
            kept = 0
            for r in json.loads(res.stdout):
                name = r["fullName"]
                if r["isArchived"] or name.lower() in seen or (r.get("pushedAt") or "")[:10] < a.pushed_since:
                    continue
                seen.add(name.lower())
                fh.write(json.dumps({
                    "url": f"https://github.com/{name}", "title": name.split("/", 1)[1], "kind": "repo", "area": a.area,
                    "source": f"gh search repos {q} --sort stars", "licence": (r.get("license") or {}).get("key", "") or "none",
                    "github": name, "stars": r["stargazersCount"], "free": True, "date": (r.get("pushedAt") or "")[:10],
                    "by": name.split("/", 1)[0], "preview": "", "homepage": r.get("homepage") or "",
                    "why": (r.get("description") or "").strip()[:220] or f"Top starred for '{q}'.",
                    "tags": [t for t in q.lower().split() if len(t) > 2][:5],
                }, ensure_ascii=False) + "\n")
                kept += 1
                added += 1
            print(f"{kept:3d} kept  {q}", file=sys.stderr)
            time.sleep(2)  # search API allows 30 requests a minute
    print(f"{added} repos appended to {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
