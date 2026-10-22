#!/usr/bin/env python3
"""Harvest Codrops tutorials, case studies and demos (the canonical free source of award-grade web techniques).

  ssh -f -N -L 19377:127.0.0.1:9377 laptop      # camofox runs on the laptop; Codrops sits behind a Cloudflare check
  CAMOFOX=http://127.0.0.1:19377 python3 research/tools/codrops_harvest.py --pages 8

Reads the public WordPress API through camofox, a page of 100 posts at a time, newest first. Appends to
research/ui/observations/codrops.jsonl, skipping links already there.
"""
import argparse, html, json, os, re, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API = "https://tympanus.net/codrops/wp-json/wp/v2"
CAMO = os.environ.get("CAMOFOX", "http://127.0.0.1:9377")
WHO = {"userId": "siso", "sessionKey": "default"}


def camo(method, path, body=None):
    req = urllib.request.Request(CAMO + path, method=method, data=json.dumps(body).encode() if body else None,
                                 headers={"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read() or b"{}")


def fetch_json(url):
    tab = camo("POST", "/tabs", {"url": url, **WHO})["tabId"]
    try:
        for _ in range(6):
            time.sleep(4)
            snap = camo("GET", f"/tabs/{tab}/snapshot?userId=siso&sessionKey=default").get("snapshot", "")
            m = re.search(r'- text: (".*")\s*$', snap, re.S) or re.search(r'- text: (".*?")\n', snap, re.S)
            if m:
                try:
                    return json.loads(json.loads(m.group(1)))
                except json.JSONDecodeError:
                    pass
        raise RuntimeError("no JSON in snapshot (challenge not passed?)")
    finally:
        camo("DELETE", f"/tabs/{tab}?userId=siso&sessionKey=default")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pages", type=int, default=5)
    p.add_argument("--start", type=int, default=1)
    a = p.parse_args()
    cats = {c["id"]: c["name"] for c in fetch_json(f"{API}/categories?per_page=100&_fields=id,name")}
    out = ROOT / "research" / "ui" / "observations" / "codrops.jsonl"
    seen = {json.loads(l)["url"] for l in out.read_text().split("\n") if l.strip()} if out.exists() else set()
    added = 0
    with open(out, "a", encoding="utf-8") as fh:
        for page in range(a.start, a.start + a.pages):
            try:
                posts = fetch_json(f"{API}/posts?per_page=100&page={page}&_fields=link,title,date,categories,excerpt")
            except Exception as e:
                print(f"page {page}: {e}; stopping", file=sys.stderr)
                break
            for post in posts:
                link = post["link"]
                if link in seen:
                    continue
                seen.add(link)
                names = [cats.get(c, "") for c in post.get("categories", [])]
                excerpt = re.sub(r"<[^>]+>", "", html.unescape(post.get("excerpt", {}).get("rendered", ""))).strip()
                title = html.unescape(post["title"]["rendered"])
                kind = "article" if any(n in ("Case Study", "Articles", "Inspiration") for n in names) else "tutorial"
                fh.write(json.dumps({
                    "url": link, "title": title, "kind": kind, "area": "3d-motion", "source": f"{API}/posts?page={page}",
                    "licence": "article: Codrops; demo code usually MIT", "preview": "", "free": True, "github": "", "stars": None,
                    "date": post["date"][:10], "by": "Codrops", "why": (excerpt[:200] or title),
                    "tags": ["codrops"] + [n.lower() for n in names if n][:4],
                }, ensure_ascii=False) + "\n")
                added += 1
            print(f"page {page}: {len(posts)} posts", file=sys.stderr)
    print(f"{added} Codrops posts appended to {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
