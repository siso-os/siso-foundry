#!/usr/bin/env python3
"""Import other people's curated lists from the Foundry awesome catalog into domain observations.

  python3 research/tools/awesome_import.py --domain agent-bases [--catalog PATH]

research/<domain>/lists.json says which awesome lists feed which area, with a star floor:
  {"lists": [{"list": "owner/awesome-x", "area": "harnesses", "min_stars": 50, "web": false}]}

GitHub entries become repo records carrying the list editor's own description and section heading; with
"web": true the list's non-GitHub links become site records, one per domain. Writes
research/<domain>/observations/awesome-catalog.jsonl (rewritten: it is a projection of a catalog snapshot).
"""
import argparse, json, os, sqlite3
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def default_catalog():
    root = Path(os.environ.get("FOUNDRY_DATA", "/Volumes/SISO-STORAGE-VAULT/foundry-data")).expanduser()
    found = sorted((root / "domains" / "github" / "awesome").glob("catalog_full*.sqlite"))
    return found[-1] if found else None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--domain", required=True)
    p.add_argument("--catalog")
    a = p.parse_args()
    catalog = Path(a.catalog) if a.catalog else default_catalog()
    if not catalog or not catalog.exists():
        raise SystemExit("no awesome catalog snapshot; pass --catalog")
    spec = json.loads((ROOT / "research" / a.domain / "lists.json").read_text())
    db = sqlite3.connect(f"file:{catalog}?mode=ro", uri=True)
    repos = {}
    sites = {}
    for item in spec["lists"]:
        rows = db.execute(
            """select e.target_repo, e.section, e.description, r.stars, r.description, r.archived, r.list_count
               from entry e left join repo r on r.full_name = e.target_repo
               where e.list_repo = ? and coalesce(r.stars, 0) >= ?""", (item["list"], item.get("min_stars", 0))).fetchall()
        for target, section, edesc, stars, rdesc, archived, list_count in rows:
            if archived:
                continue
            cur = repos.setdefault(target, {"area": item["area"], "lists": [], "sections": [], "desc": "", "stars": stars,
                                            "rdesc": rdesc or "", "list_count": list_count or 0})
            if item["list"] not in cur["lists"]:
                cur["lists"].append(item["list"])
            if section and section not in cur["sections"]:
                cur["sections"].append(section)
            if edesc and len(edesc) > len(cur["desc"]):
                cur["desc"] = edesc
        if item.get("web"):
            for url, dom, label, section, desc in db.execute(
                    "select url, domain, label, section, description from weblink where list_repo = ?", (item["list"],)):
                if dom in ("github.com", "twitter.com", "x.com", "youtube.com", "medium.com", "reddit.com"):
                    continue
                s = sites.setdefault(dom, {"url": url, "label": label or dom, "area": item["area"], "lists": [], "sections": [], "desc": ""})
                if item["list"] not in s["lists"]:
                    s["lists"].append(item["list"])
                if section and section not in s["sections"]:
                    s["sections"].append(section)
                if desc and len(desc) > len(s["desc"]):
                    s["desc"] = desc
    out = ROOT / "research" / a.domain / "observations" / "awesome-catalog.jsonl"
    snap = catalog.name
    with open(out, "w", encoding="utf-8") as fh:
        for target, r in sorted(repos.items()):
            what = (r["desc"] or r["rdesc"]).strip().replace("\n", " ")[:220]
            fh.write(json.dumps({
                "url": f"https://github.com/{target}", "title": target.split("/", 1)[1], "kind": "repo", "area": r["area"],
                "source": f"https://github.com/{r['lists'][0]}", "also_in": r["lists"][1:], "licence": "", "github": target,
                "stars": r["stars"], "free": True, "date": "", "by": target.split("/", 1)[0], "preview": "",
                "why": (what + f" (listed by {len(r['lists'])} of our lists; {r['list_count']} lists catalog-wide)").strip(),
                "tags": [s.lower()[:30] for s in r["sections"][:4]], "catalog": snap,
            }, ensure_ascii=False) + "\n")
        for dom, s in sorted(sites.items()):
            fh.write(json.dumps({
                "url": s["url"], "title": s["label"][:80], "kind": "site", "area": s["area"], "source": f"https://github.com/{s['lists'][0]}",
                "also_in": s["lists"][1:], "licence": "unknown", "github": "", "stars": None, "free": None, "date": "", "by": "",
                "preview": "", "why": (s["desc"] or "").strip().replace("\n", " ")[:220], "tags": [x.lower()[:30] for x in s["sections"][:4]],
                "catalog": snap,
            }, ensure_ascii=False) + "\n")
    print(f"{a.domain}: {len(repos)} repos, {len(sites)} sites from {len(spec['lists'])} lists -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
