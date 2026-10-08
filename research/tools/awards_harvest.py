#!/usr/bin/env python3
"""Harvest award-winning sites from the public Awwwards archives into UI observations.

  python3 research/tools/awards_harvest.py --pages 20                 Sites of the Day, newest first
  python3 research/tools/awards_harvest.py --list sites_of_the_month --pages 5

Each card carries the award's own JSON (title, date, technology tags, thumbnail) and the live site link.
Public pages only, one request at a time with a pause. Appends to research/ui/observations/awwwards.jsonl,
skipping sites already there.
"""
import argparse, html, json, re, sys, time, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
LABEL = {"sites_of_the_day": "Awwwards Site of the Day", "sites_of_the_month": "Awwwards Site of the Month",
         "sites_of_the_year": "Awwwards Site of the Year nominee", "developer": "Awwwards Developer Award",
         "honorable": "Awwwards Honorable Mention", "nominees": "Awwwards nominee"}
TECH = {"three.js", "webgl", "gsap", "next.js", "react", "vue.js", "nuxt", "webflow", "framer", "svelte", "astro", "lenis",
        "barba.js", "pixijs", "spline", "shopify", "wordpress", "tailwind", "lottie", "rive", "webgpu", "glsl", "r3f"}


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def cards(page_html):
    for chunk in page_html.split('<li class="col-3 js-collectable"')[1:]:
        m = re.search(r'data-collectable-model-value="([^"]+)"', chunk)
        if not m:
            continue
        model = json.loads(html.unescape(m.group(1)))
        if model.get("type") != "submission":
            continue
        site = re.search(r'class="figure-rollover__bt"\s+href="(https?://[^"]+)"', chunk)
        by = re.search(r'class="avatar-name__link" href="/([^"/]+)/"', chunk)
        by_name = re.search(r'class="avatar-name__title[^"]*"[^>]*>\s*([^<]+?)\s*<', chunk)
        yield model, site.group(1) if site else "", (by_name.group(1) if by_name else (by.group(1) if by else ""))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--list", default="sites_of_the_day", choices=sorted(LABEL))
    p.add_argument("--pages", type=int, default=10)
    p.add_argument("--start", type=int, default=1)
    p.add_argument("--pause", type=float, default=2.0)
    a = p.parse_args()
    out = ROOT / "research" / "ui" / "observations" / "awwwards.jsonl"
    seen = {json.loads(l)["source"] for l in out.read_text().split("\n") if l.strip()} if out.exists() else set()
    added = 0
    with open(out, "a", encoding="utf-8") as fh:
        for page in range(a.start, a.start + a.pages):
            url = f"https://www.awwwards.com/websites/{a.list}/?page={page}"
            try:
                found = list(cards(get(url)))
            except Exception as e:
                print(f"page {page}: {type(e).__name__}; stopping", file=sys.stderr)
                break
            if not found:
                print(f"page {page}: no cards; stopping", file=sys.stderr)
                break
            for model, site, by in found:
                source = f"https://www.awwwards.com/sites/{model['slug']}"
                if source in seen or not site:
                    continue
                seen.add(source)
                thumb = (model.get("images") or {}).get("thumbnail") or model.get("collectableImage") or ""
                tags = [t for t in model.get("tags") or []]
                tech = [t for t in tags if t.lower() in TECH]
                date = datetime.fromtimestamp(model["createdAt"], timezone.utc).strftime("%Y-%m-%d") if model.get("createdAt") else ""
                fh.write(json.dumps({
                    "url": site, "title": html.unescape(model.get("title", "")), "kind": "site", "area": "awards", "source": source,
                    "licence": "proprietary (reference only)", "free": None, "github": "", "stars": None, "date": date, "by": by,
                    "preview": f"https://assets.awwwards.com/awards/media/cache/thumb_880_660/{thumb}" if thumb else "",
                    "why": f"{LABEL[a.list]} {date}" + (f"; built with {', '.join(tech)}" if tech else "") + f"; {', '.join(t for t in tags if t not in tech)[:120]}.",
                    "tags": [t.lower() for t in tags][:8], "award": LABEL[a.list],
                }, ensure_ascii=False) + "\n")
                added += 1
            print(f"page {page}: {len(found)} cards", file=sys.stderr)
            time.sleep(a.pause)
    print(f"{added} sites appended to {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
