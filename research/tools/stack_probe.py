#!/usr/bin/env python3
"""Detect what award-winning sites actually ship: read each site's HTML and first scripts for library signatures.

  python3 research/tools/stack_probe.py [--area awards] [--limit 0] [--workers 12]
  python3 research/tools/stack_probe.py --report          share of sites per library, by award year

Appends one line per site to research/ui/stacks.jsonl: {"url", "at", "stack": [...], "scripts": n}. `foundry build`
adds "uses:<lib>" tags. Signatures are strings the libraries leave in shipped code, so a hit is evidence, not a guess;
a miss can mean the code sits in a script we did not read (we read the page and up to six same-site scripts).
"""
import argparse, collections, concurrent.futures as cf, json, re, sys, time, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
SIGNS = {
    "three.js": [r"WebGLRenderer", r"__THREE__", r"three\.module", r"three@\d"],
    "react-three-fiber": [r"@react-three/fiber", r"useFrame\b.{0,40}useThree", r"r3f"],
    "ogl": [r"\bogl\b.{0,20}Renderer", r"from\s*['\"]ogl['\"]"],
    "pixi.js": [r"PIXI\.", r"pixi\.js"],
    "babylon.js": [r"BABYLON\.", r"babylonjs"],
    "playcanvas": [r"playcanvas"],
    "webgpu": [r"navigator\.gpu", r"GPUCanvasContext"],
    "gsap": [r"gsap\.", r"GreenSock", r"\bgsap\b"],
    "scrolltrigger": [r"ScrollTrigger"],
    "lenis": [r"\blenis\b", r"Lenis\("],
    "locomotive-scroll": [r"locomotive-scroll", r"LocomotiveScroll"],
    "barba.js": [r"@barba/core", r"barba\.init", r"data-barba"],
    "swup": [r"\bswup\b"],
    "motion": [r"framer-motion", r"motion/react", r"motion\.dev"],
    "theatre.js": [r"@theatre/core", r"theatrejs"],
    "lottie": [r"lottie", r"bodymovin"],
    "rive": [r"@rive-app", r"\.riv['\"]"],
    "spline": [r"@splinetool", r"spline\.design", r"prod\.spline"],
    "unicorn-studio": [r"unicornstudio", r"UnicornStudio"],
    "matter.js": [r"Matter\.Engine", r"matter-js"],
    "next.js": [r"/_next/static", r"__NEXT_DATA__"],
    "nuxt": [r"/_nuxt/", r"__NUXT__"],
    "astro": [r"astro-island", r"/_astro/"],
    "sveltekit": [r"__sveltekit", r"/_app/immutable"],
    "vue": [r"data-v-[0-9a-f]{8}", r"__VUE__"],
    "webflow": [r"webflow\.com", r"data-wf-page", r"Webflow\.push"],
    "framer": [r"framerusercontent", r"__framer"],
    "shopify": [r"cdn\.shopify\.com", r"Shopify\.theme"],
    "wordpress": [r"wp-content/", r"wp-includes/"],
    "prismic": [r"prismic\.io"],
    "sanity": [r"cdn\.sanity\.io"],
    "storyblok": [r"storyblok"],
    "tailwind": [r"tailwindcss", r"--tw-"],
}
COMPILED = {k: [re.compile(p, re.I) for p in v] for k, v in SIGNS.items()}


def get(url, limit):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read(limit).decode("utf-8", "replace"), r.geturl()


def probe(url):
    try:
        page, final = get(url, 1_500_000)
    except Exception as e:
        return {"url": url, "at": time.strftime("%Y-%m-%d"), "error": type(e).__name__, "stack": []}
    host = urllib.parse.urlparse(final).netloc
    texts = [page]
    srcs = re.findall(r"<script[^>]+src=[\"']([^\"']+)[\"']", page, re.I)
    same = [urllib.parse.urljoin(final, s) for s in srcs]
    same = [s for s in same if urllib.parse.urlparse(s).netloc in (host, "") or "cdn" in s][:6]
    for s in same:
        try:
            texts.append(get(s, 3_000_000)[0])
        except Exception:
            pass
    blob = "\n".join(texts) + "\n".join(srcs)
    stack = [k for k, pats in COMPILED.items() if any(p.search(blob) for p in pats)]
    if "react-three-fiber" in stack and "three.js" not in stack:
        stack.append("three.js")
    return {"url": url, "at": time.strftime("%Y-%m-%d"), "stack": sorted(stack), "scripts": len(texts) - 1}


def report():
    stacks = {s["url"]: s for s in map(json.loads, filter(str.strip, (ROOT / "research/ui/stacks.jsonl").read_text().split("\n")))}
    recs = [json.loads(l) for l in (ROOT / "research/ui/records.jsonl").read_text().split("\n") if l.strip()]
    by, n = collections.defaultdict(collections.Counter), collections.Counter()
    for r in recs:
        s = stacks.get(r["url"])
        if r.get("area") != "awards" or not s or s.get("error"):
            continue
        y = (r.get("date") or "")[:4] or "undated"
        n[y] += 1
        by[y].update(s["stack"])
    for y in sorted(n, reverse=True):
        if n[y] >= 20:
            print(f"{y} ({n[y]} sites): " + ", ".join(f"{k} {100 * c // n[y]}%" for k, c in by[y].most_common(14)))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--area", default="awards")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--workers", type=int, default=12)
    p.add_argument("--report", action="store_true")
    a = p.parse_args()
    if a.report:
        return report()
    out = ROOT / "research" / "ui" / "stacks.jsonl"
    done = {json.loads(l)["url"] for l in out.read_text().split("\n") if l.strip()} if out.exists() else set()
    recs = [json.loads(l) for l in (ROOT / "research/ui/records.jsonl").read_text().split("\n") if l.strip()]
    todo = [r["url"] for r in recs if r.get("area") == a.area and r.get("kind") == "site" and r["url"] not in done]
    todo = todo[: a.limit] if a.limit else todo
    print(f"probing {len(todo)} sites", file=sys.stderr)
    with open(out, "a", encoding="utf-8") as fh, cf.ThreadPoolExecutor(a.workers) as pool:
        for i, res in enumerate(pool.map(probe, todo), 1):
            fh.write(json.dumps(res) + "\n")
            if i % 100 == 0:
                print(f"  {i}/{len(todo)}", file=sys.stderr)


if __name__ == "__main__":
    main()
