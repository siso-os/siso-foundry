#!/usr/bin/env python3
"""Record the studios and developers who win web awards most often, with their own site and the stack they ship.

  python3 research/tools/studios.py [--min-wins 5] [--workers 3]

Counts award records in research/ui/records.jsonl by maker, then for each maker with at least --min-wins reads one of
their Awwwards site pages (for the Awwwards username) and the Awwwards profile (for their own website, avatar and
one-line description). Stack shares come from the uses:<lib> tags stack_probe.py left on their winners. Rewrites
research/ui/observations/studios.jsonl (a projection of the award records plus profile facts).
"""
import argparse, collections, concurrent.futures as cf, html, json, re, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
LIBS = ["gsap", "lenis", "three.js", "r3f", "webgl", "ogl", "nuxt", "vue", "next.js", "webflow", "barba", "lottie"]


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def profile(maker, pages):
    """Awwwards username from a winner page, then website/avatar/description from the profile."""
    for page in pages[:3]:
        try:
            s = html.unescape(get(page))
        except Exception:
            continue
        m = re.search(r'"username":"([^"]+)","displayName":"' + re.escape(maker.replace("/", "\\/")) + '"', s)
        if not m:
            continue
        user = m.group(1)
        url = f"https://www.awwwards.com/{user}/"
        try:
            p = get(url)
        except Exception:
            return {"profile": url}
        site = re.search(r'class="toolbar-bts__item" href="(https?://[^"]+)"', p)
        img = re.search(r'property="og:image" content="([^"]+)"|"og:image" content="([^"]+)"', p)
        desc = re.search(r'og:description" content="([^"]*)"', p)
        return {"profile": url, "site": site.group(1) if site and "awwwards.com" not in site.group(1) else "",
                "avatar": (img.group(1) or img.group(2)) if img else "", "desc": html.unescape(desc.group(1)) if desc else ""}
    return {}


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--min-wins", type=int, default=5)
    a.add_argument("--workers", type=int, default=3)
    a = a.parse_args()
    makers = collections.defaultdict(lambda: {"wins": 0, "awards": collections.Counter(), "libs": collections.Counter(),
                                              "pages": [], "years": collections.Counter(), "examples": []})
    for line in (ROOT / "research" / "ui" / "records.jsonl").read_text().split("\n"):
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("area") != "awards" or not r.get("by"):
            continue
        m = makers[r["by"].strip()]
        m["wins"] += 1
        m["awards"][r.get("award") or "award"] += 1
        m["years"][(r.get("date") or "")[:4]] += 1
        for t in r.get("tags") or []:
            if t.startswith("uses:"):
                m["libs"][t[5:]] += 1
        m["pages"] += [s for s in [r.get("source", "")] + (r.get("sources") or []) if "awwwards.com/sites/" in str(s)]
        if len(m["examples"]) < 3:
            m["examples"].append(r["title"])
    top = sorted(((k, v) for k, v in makers.items() if v["wins"] >= a.min_wins), key=lambda x: -x[1]["wins"])
    print(f"{len(top)} makers with {a.min_wins}+ wins", file=sys.stderr)
    with cf.ThreadPoolExecutor(a.workers) as pool:
        facts = list(pool.map(lambda kv: profile(kv[0], kv[1]["pages"]), top))
    out = ROOT / "research" / "ui" / "observations" / "studios.jsonl"
    n = 0
    with open(out, "w", encoding="utf-8") as fh:
        for (name, m), f in zip(top, facts):
            url = f.get("site") or f.get("profile")
            if not url:
                continue
            probed = sum(m["libs"].values()) and m["wins"]
            libs = [f"{lib} {100 * m['libs'][lib] // m['wins']}%" for lib in LIBS if m["libs"][lib] * 4 >= m["wins"]]
            years = sorted(y for y in m["years"] if y)
            fh.write(json.dumps({
                "url": url, "title": name, "kind": "studio", "area": "people", "source": f.get("profile") or "award records",
                "licence": "proprietary (reference only)", "preview": f.get("avatar", ""), "github": "", "stars": None,
                "free": None, "date": time.strftime("%Y-%m-%d"), "by": name,
                "why": (f"{m['wins']} web awards {years[0]}-{years[-1]} (" + ", ".join(f"{c} {k}" for k, c in m["awards"].most_common(3))
                        + ")" + (f"; ships {', '.join(libs)}" if probed and libs else "") + f"; e.g. {', '.join(m['examples'])}."
                        + (f" {f['desc'][:160]}" if f.get("desc") else "")),
                "tags": ["studio", "award-winner"] + [f"uses:{lib}" for lib in LIBS if m["libs"][lib] * 4 >= m["wins"]],
                "awwwards": f.get("profile", ""), "wins": m["wins"],
            }, ensure_ascii=False) + "\n")
            n += 1
    print(f"{n} studios -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
