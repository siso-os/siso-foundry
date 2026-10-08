#!/usr/bin/env python3
"""Harvest award-winning and curated sites beyond Awwwards into UI observations.

  python3 research/tools/awards_more.py cssda --pages 10              CSS Design Awards Website of the Day, newest first
  python3 research/tools/awards_more.py cssda --list woty --pages 1   CSS Design Awards Website of the Year
  python3 research/tools/awards_more.py fwa --pages 10                The FWA (FWA of the Day / of the Month), newest first
  python3 research/tools/awards_more.py godly                         Godly picks (godly.website now redirects to recent.design/websites)
  python3 research/tools/awards_more.py onepagelove --pages 10        One Page Love picks, newest first

Each source is read from its own public card data: the live site link, award date, studio, tags and the
award's own thumbnail as preview. Public pages only, one request at a time with a pause, browser user agent.
Appends to research/ui/observations/awards-more.jsonl, skipping sites (urls) already there.
Blocked when probed on 2026-10-08: siteinspire.com (Vercel checkpoint, 429), lapa.ninja (Cloudflare, 403).
"""
import argparse, html, json, re, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "research" / "ui" / "observations" / "awards-more.jsonl"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
TECH = {"three.js", "webgl", "gsap", "next.js", "react", "vue.js", "nuxt", "webflow", "framer", "svelte", "astro", "lenis",
        "barba.js", "pixijs", "spline", "shopify", "wordpress", "tailwind", "tailwind css", "lottie", "rive", "webgpu", "glsl", "r3f"}
MONTHS = {m: i for i, m in enumerate(["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"], 1)}
PAUSE = 2.0


def get(url, accept="text/html"):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode("utf-8", "replace")
    time.sleep(PAUSE)
    return body


def clean_url(u):
    """Live site URL without gallery referral parameters."""
    p = urllib.parse.urlsplit(html.unescape(u).strip())
    q = [(k, v) for k, v in urllib.parse.parse_qsl(p.query) if k.lower() not in ("ref", "utm_source", "utm_medium", "utm_campaign")]
    return urllib.parse.urlunsplit((p.scheme, p.netloc, p.path or "/", urllib.parse.urlencode(q), ""))


def key(u):
    p = urllib.parse.urlsplit(u.lower())
    return p.netloc.removeprefix("www.") + p.path.rstrip("/")


def record(url, title, source, date, by, preview, award, tags, about=""):
    tags = [t for t in dict.fromkeys(t.strip().lower() for t in tags if t and t.strip())]
    tech = [t for t in tags if t in TECH]
    rest = ", ".join(t for t in tags if t not in tech)
    why = f"{award} {date}".strip() + (f"; built with {', '.join(tech)}" if tech else "") + (f"; {rest[:120]}" if rest else "")
    if about:
        why += f"; {about[:160]}"
    return {"url": url, "title": title, "kind": "site", "area": "awards", "source": source,
            "licence": "proprietary (reference only)", "free": None, "github": "", "stars": None, "date": date, "by": by,
            "preview": preview, "why": why.rstrip(".") + ".", "tags": tags[:8], "award": award}


# ---- CSS Design Awards -------------------------------------------------------------------------------------------
CSSDA_LABEL = {"wotd": "CSS Design Awards Website of the Day", "wotm": "CSS Design Awards Website of the Month",
               "woty": "CSS Design Awards Website of the Year"}


def cssda_detail(source):
    """By, exact date and tags from the site's CSSDA page (text lines between the award line and CATEGORY:)."""
    txt = re.sub(r"<script.*?</script>|<style.*?</style>", "", get(source), flags=re.S)
    lines = [html.unescape(l).strip() for l in re.sub(r"<[^>]+>", "\n", txt).split("\n")]
    lines = [l for l in lines if l and l != ","]
    out = {}
    for i, l in enumerate(lines):
        m = re.match(r"Website Of The (?:Day|Month|Year) (\d{4})(?: (\w{3}) (\d{1,2}))?", l)
        if m and "by" not in out:
            if m.group(2):
                out["date"] = f"{m.group(1)}-{MONTHS.get(m.group(2).upper(), 1):02d}-{int(m.group(3)):02d}"
            out["by"] = lines[i + 2] if i + 2 < len(lines) and lines[i + 2] != "ABOUT:" else ""
        if l == "ABOUT:" and i + 1 < len(lines):
            out["about"] = lines[i + 1]
        if l == "TAGS:":
            j, tags = i + 1, []
            while j < len(lines) and not lines[j].endswith(":"):
                tags.append(lines[j]); j += 1
            out["tags"] = tags
    return out


def cssda(a, seen, emit):
    label = CSSDA_LABEL[a.list]
    for page in range(a.start, a.start + a.pages):
        page_html = get(f"https://www.cssdesignawards.com/{a.list}-award-winners?page={page}")
        found = page_html.split('<article class="single-project">')[1:]
        if not found:
            print(f"cssda page {page}: no cards; stopping", file=sys.stderr)
            return
        for chunk in found:
            site = re.search(r'href="(https?://[^"]+)"[^>]*class="sp__project-link"', chunk)
            src = re.search(r'href="(/sites/[^"]+)"', chunk)
            if not site or not src:
                continue
            url = clean_url(site.group(1))
            if key(url) in seen or "cssdesignawards.com" in url:
                continue
            seen.add(key(url))
            source = "https://www.cssdesignawards.com" + src.group(1)
            img = re.search(r'<img src="(/cdasites/(\d{4})/\d{4}(\d{2})/[^"]+)"', chunk)
            title = re.search(r'single-project__title"><a [^>]+>([^<]+)<', chunk)
            when = re.search(r'sp__meta__date">([^<]+)<', chunk)
            score = re.search(r"JPANEL ([\d.]+)", chunk)
            date = ""
            if img and when:  # card shows "OCT 8"; the thumbnail path carries the upload year and month
                mo, _, day = when.group(1).strip().partition(" ")
                if mo.upper() in MONTHS and day.isdigit():
                    y = int(img.group(2)) + (1 if MONTHS[mo.upper()] < int(img.group(3)) else 0)
                    date = f"{y}-{MONTHS[mo.upper()]:02d}-{int(day):02d}"
                elif re.fullmatch(r"\d{4}", when.group(1).strip()):
                    date = when.group(1).strip()
            info = cssda_detail(source) if a.detail else {}
            about = info.get("about", "") + (f" (judges {score.group(1)}/10)" if score else "")
            emit(record(url, html.unescape(title.group(1)).strip() if title else "", source, info.get("date") or date,
                        info.get("by", ""), "https://www.cssdesignawards.com" + img.group(1) if img else "", label,
                        info.get("tags", []), about.strip()))
        print(f"cssda page {page}: {len(found)} cards", file=sys.stderr)


# ---- The FWA ------------------------------------------------------------------------------------------------------
def fwa_thumb(item):
    th = item.get("thumbnail") or {}
    for size, span in (("958", "span6"), ("958", "span5"), ("1364", "span4"), ("538", "span12")):
        p = (th.get(size) or {}).get(span)
        if p:
            return "https://thefwa.com" + p
    return ""


def fwa(a, seen, emit):
    for page in range(a.start, a.start + a.pages):
        data = json.loads(get(f"https://thefwa.com/api/timeline/?slug=awards&limit=20&offset={(page - 1) * 20}", "application/json"))
        items = data.get("items") or []
        if not items:
            print(f"fwa page {page}: no items; stopping", file=sys.stderr)
            return
        for entry in items:
            it = entry.get("item") or {}
            if entry.get("type") != "awards" or not it.get("url"):
                continue
            url = clean_url(it["url"])
            if not url.startswith("http") or key(url) in seen or "thefwa.com" in url:
                continue
            seen.add(key(url))
            by = ", ".join(p.get("name", "") for p in (it.get("profiles") or [])[:3] if p.get("name"))
            tags = [c.get("name", "") for c in it.get("categories") or []] + [(it.get("caseTypes") or {}).get("name", "")]
            score = f" (jury {it['points']}/100)" if it.get("points") else ""
            emit(record(url, html.unescape(it.get("title", "")), f"https://thefwa.com/cases/{it.get('slug', '')}",
                        entry.get("sortDate", ""), by, fwa_thumb(it), entry.get("title") or "FWA award", tags,
                        (it.get("description") or "").strip().replace("\n", " ") + score))
        print(f"fwa page {page}: {len(items)} items", file=sys.stderr)
        if not data.get("next"):
            return


# ---- Godly (now recent.design) ----------------------------------------------------------------------------------
def js_str(s):
    try:
        return json.loads(f'"{s}"')
    except ValueError:
        return s


GODLY_ITEM = re.compile(r'\$R\[\d+\]=\{id:"(\w+)",slug:"([^"]+)",title:"((?:[^"\\]|\\.)*)",format:"site"')


def godly(a, seen, emit):
    first = get("https://recent.design/websites")
    cats = [c for c, n in re.findall(r'\{id:"cat_web_[^"]+",slug:"([^"]+)",name:"[^"]+",scope:"web",sortOrder:\d+,postCount:(\d+)', first) if int(n) > 0]
    pages = [("https://recent.design/websites", first)] + [(f"https://recent.design/websites?category={c}", None) for c in cats]
    rows = {}
    for url, body in pages:
        body = body or get(url)
        starts = list(GODLY_ITEM.finditer(body))
        for n, m in enumerate(starts):
            seg = body[m.start(): starts[n + 1].start() if n + 1 < len(starts) else len(body)]
            site = re.search(r'source:\$R\[\d+\]=\{id:"[^"]+",type:"website",url:"([^"]+)"', seg)
            if not site or m.group(1) in rows:
                continue
            poster = re.search(r'poster:\$R\[\d+\]=\{key:"[^"]+",url:"([^"]+)"', seg) or \
                re.search(r'(?:cover|media):\$R\[\d+\]=\[?\$R\[\d+\]=\{url:"([^"]+\.(?:webp|jpg|png))"', seg)
            pub = re.search(r"publishedAt:(\d+)", seg)
            desc = re.search(r'description:"((?:[^"\\]|\\.)*)"', seg)
            tags = re.findall(r'context:"\w+",slug:"[^"]+",name:"([^"]+)"', seg)
            cat = re.search(r'category:\$R\[\d+\]=\{id:"[^"]+",slug:"[^"]+",name:"([^"]+)"', seg)
            staff = re.search(r"staffPickAt:(\d+)", seg)
            rows[m.group(1)] = (int(pub.group(1)) if pub else 0, m, site.group(1), poster.group(1) if poster else "",
                                js_str(desc.group(1)) if desc else "", ([cat.group(1)] if cat else []) + tags, bool(staff))
        print(f"godly {url}: {len(starts)} items", file=sys.stderr)
    for pub, m, site, poster, desc, tags, staff in sorted(rows.values(), key=lambda r: -r[0]):
        url = clean_url(js_str(site))
        if not url.startswith("http") or key(url) in seen or "recent.design" in url or "godly.website" in url:
            continue
        seen.add(key(url))
        date = datetime.fromtimestamp(pub / 1000, timezone.utc).strftime("%Y-%m-%d") if pub else ""
        emit(record(url, js_str(m.group(3)), f"https://recent.design/i/{m.group(1)}-{m.group(2)}", date, "", poster,
                    "Godly pick", tags + (["staff pick"] if staff else []), desc))


# ---- One Page Love ------------------------------------------------------------------------------------------------
def onepagelove(a, seen, emit):
    for page in range(a.start, a.start + a.pages):
        page_html = get("https://onepagelove.com/inspiration" + (f"/page/{page}" if page > 1 else ""))
        found = page_html.split('<div class="thumb-wrap thumb-loop">')[1:]
        if not found:
            print(f"onepagelove page {page}: no cards; stopping", file=sys.stderr)
            return
        for chunk in found:
            src = re.search(r'<a href="(https://onepagelove\.com/[^"]+)" title="([^"]*)"', chunk)
            site = re.search(r'class="thumb-link">.*?<a href="(https?://[^"]+)"', chunk, re.S)
            if not src or not site:
                continue
            url = clean_url(site.group(1))
            if key(url) in seen or "onepagelove.com" in url:
                continue
            seen.add(key(url))
            img = re.search(r'srcset="[^"]*?, (https://assets\.onepagelove\.com/\S+) 840w', chunk) or re.search(r'src="(https://assets\.onepagelove\.com/[^"]+)"', chunk) \
                or re.search(r'poster="(https://onepagelove\.com/[^"]+)"', chunk)
            ym = re.search(r"/uploads/(\d{4})/(\d{2})/", chunk)
            tags = re.findall(r'rel="category">([^<]+)<', chunk)
            emit(record(url, html.unescape(src.group(2)), src.group(1), f"{ym.group(1)}-{ym.group(2)}" if ym else "", "",
                        img.group(1) if img else "", "One Page Love pick", [html.unescape(t) for t in tags]))
        print(f"onepagelove page {page}: {len(found)} cards", file=sys.stderr)


SOURCES = {"cssda": cssda, "fwa": fwa, "godly": godly, "onepagelove": onepagelove}


def main():
    global PAUSE
    p = argparse.ArgumentParser()
    p.add_argument("source", choices=sorted(SOURCES))
    p.add_argument("--list", default="wotd", choices=sorted(CSSDA_LABEL), help="cssda only")
    p.add_argument("--pages", type=int, default=5)
    p.add_argument("--start", type=int, default=1)
    p.add_argument("--pause", type=float, default=2.0)
    p.add_argument("--no-detail", dest="detail", action="store_false", help="cssda: skip the per-site page (by, tags, exact date)")
    a = p.parse_args()
    PAUSE = a.pause
    seen = {key(json.loads(l)["url"]) for l in OUT.read_text().split("\n") if l.strip()} if OUT.exists() else set()
    added = 0
    with open(OUT, "a", encoding="utf-8") as fh:
        def emit(rec):
            nonlocal added
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            added += 1
        try:
            SOURCES[a.source](a, seen, emit)
        except Exception as e:
            print(f"{a.source}: {type(e).__name__}: {e}; stopping", file=sys.stderr)
    print(f"{added} sites appended to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
