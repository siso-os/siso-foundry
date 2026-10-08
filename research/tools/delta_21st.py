#!/usr/bin/env python3
"""Record the 21st.dev items the component bank lacks (title, description, preview) so lookups cover all of 21st.dev.

  python3 research/tools/delta_21st.py <list.txt> [--workers 4]

The list comes from sitemap_21st.py --bank-index. Each public page's own meta tags give the title, description and
preview image. Appends to research/ui/observations/21st-delta.jsonl, skipping URLs already there.
"""
import argparse, concurrent.futures as cf, json, re, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from probe import fetch  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
KIND = {"components": "component", "themes": "theme", "templates": "template", "library": "library"}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("urls")
    p.add_argument("--workers", type=int, default=4)
    a = p.parse_args()
    out = ROOT / "research" / "ui" / "observations" / "21st-delta.jsonl"
    seen = {json.loads(l)["url"] for l in out.read_text().split("\n") if l.strip()} if out.exists() else set()
    todo = [u.strip() for u in Path(a.urls).read_text().split("\n") if u.strip() and u.strip() not in seen]
    print(f"fetching {len(todo)} pages", file=sys.stderr)
    ok = 0
    with open(out, "a", encoding="utf-8") as fh, cf.ThreadPoolExecutor(a.workers) as pool:
        for i, (url, res) in enumerate(zip(todo, pool.map(fetch, todo)), 1):
            if res.get("status") != 200 or not res.get("og_title"):
                continue
            author, section = url.replace("https://21st.dev/", "").split("/")[:2]
            title = re.sub(r"\s*\|.*$", "", res["og_title"]).strip()
            fh.write(json.dumps({
                "url": url, "title": title, "kind": KIND.get(section, section), "area": "components",
                "source": "https://21st.dev/sitemap.xml", "licence": "21st.dev community (per author)", "preview": res.get("og_image", ""),
                "why": res.get("og_description", "") or title, "tags": ["21st.dev", KIND.get(section, section)], "github": "",
                "stars": None, "free": None, "date": time.strftime("%Y-%m-%d"), "by": author.lstrip("@"),
            }, ensure_ascii=False) + "\n")
            ok += 1
            if i % 250 == 0:
                print(f"  {i}/{len(todo)}", file=sys.stderr)
    print(f"{ok} items appended to {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
