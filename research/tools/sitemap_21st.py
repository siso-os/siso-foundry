#!/usr/bin/env python3
"""Map 21st.dev from its public sitemap: authors, catalogue sections, and what the SISO component bank lacks.

  python3 research/tools/sitemap_21st.py [--bank-index PATH] [--min-items 5]

Writes research/ui/observations/21st-sitemap.jsonl (rewritten: a projection of today's sitemap): one record per
author with at least --min-items items and one per catalogue section. With the component bank's index.jsonl it
also writes the URLs the bank lacks to the data plane and prints the counts, for the bank's owner to pull.
"""
import argparse, collections, json, os, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--bank-index")
    p.add_argument("--min-items", type=int, default=5)
    a = p.parse_args()
    req = urllib.request.Request("https://21st.dev/sitemap.xml", headers={"User-Agent": UA})
    xml = urllib.request.urlopen(req, timeout=60).read().decode()
    urls = [u.split("</loc>")[0] for u in xml.split("<loc>")[1:]]
    authors, sections = collections.defaultdict(collections.Counter), collections.Counter()
    for u in urls:
        parts = u.replace("https://21st.dev/", "").split("/")
        if parts[0].startswith("@") and len(parts) >= 3:
            authors[parts[0]][parts[1]] += 1
            sections[parts[1]] += 1
        elif parts[0] == "community" and len(parts) >= 3:
            sections["community/" + parts[1]] += 1
    today = time.strftime("%Y-%m-%d")
    out = ROOT / "research" / "ui" / "observations" / "21st-sitemap.jsonl"
    with open(out, "w", encoding="utf-8") as fh:
        for sec, n in sections.most_common():
            path = sec if sec.startswith("community/") else f"community/{sec}"
            fh.write(json.dumps({"url": f"https://21st.dev/{path}", "title": f"21st.dev {sec.replace('community/', '')}",
                                 "kind": "directory", "area": "components", "source": "https://21st.dev/sitemap.xml",
                                 "licence": "per item", "preview": "", "free": None, "github": "", "stars": None, "date": today,
                                 "by": "21st.dev", "why": f"21st.dev catalogue section with {n} items in its sitemap on {today}.",
                                 "tags": ["21st.dev", sec.split("/")[-1]]}) + "\n")
        for author, kinds in sorted(authors.items(), key=lambda x: -sum(x[1].values())):
            total = sum(kinds.values())
            if total < a.min_items:
                continue
            fh.write(json.dumps({"url": f"https://21st.dev/{author}", "title": f"{author} on 21st.dev", "kind": "person",
                                 "area": "components", "source": "https://21st.dev/sitemap.xml", "licence": "per item",
                                 "preview": "", "free": None, "github": "", "stars": None, "date": today, "by": author[1:],
                                 "why": f"21st.dev author with {total} items: " + ", ".join(f"{n} {k}" for k, n in kinds.most_common()) + ".",
                                 "tags": ["21st.dev", "21st-author"]}) + "\n")
    print(f"{len(urls)} sitemap urls, {len(authors)} authors ({sum(1 for k in authors.values() if sum(k.values()) >= a.min_items)} recorded), {len(sections)} sections")
    if a.bank_index:
        have = {json.loads(l).get("url", "").rstrip("/").lower() for l in Path(a.bank_index).read_text().split("\n") if l.strip()}
        missing = [u for u in urls if u.rstrip("/").lower() not in have and "/" in u.replace("https://21st.dev/", "")
                   and u.replace("https://21st.dev/", "").split("/")[0].startswith("@")]
        root = Path(os.environ.get("FOUNDRY_DATA", "/Volumes/SISO-STORAGE-VAULT/foundry-data")).expanduser()
        dest = root / "research" / "ui" / f"21st-not-in-component-bank-{today}.txt"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text("\n".join(missing) + "\n")
        kinds = collections.Counter(u.replace("https://21st.dev/", "").split("/")[1] for u in missing)
        print(f"{len(missing)} author items not in the component bank ({dict(kinds)}) -> {dest}")


if __name__ == "__main__":
    main()
