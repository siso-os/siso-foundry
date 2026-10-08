#!/usr/bin/env python3
"""Check every record against the live source, so a record is evidence and not a helper's claim.

  python3 research/tools/probe.py web --domain ui [--all]   fetch each URL: status, og:image, og:title
  python3 research/tools/probe.py github --domain ui        stars, licence, archived, pushed, description per repo

Results are append-only facts beside the records: research/<domain>/probes.jsonl and github.jsonl.
`foundry build` folds them in: a preview from og:image where the record had none, and live stars and licence.
"""
import argparse, concurrent.futures as cf, html, json, re, subprocess, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
META = re.compile(r"<meta\b[^>]*>", re.I)


def attr(tag, name):
    m = re.search(name + r"""\s*=\s*["']([^"']*)["']""", tag, re.I)
    return html.unescape(m.group(1)).strip() if m else ""


def fetch(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*"})
        with urllib.request.urlopen(req, timeout=15) as r:
            body = r.read(400_000).decode("utf-8", "replace")
            status, final = r.status, r.geturl()
    except urllib.error.HTTPError as e:
        return {"status": e.code}
    except Exception as e:  # dns, tls, timeout: the record stays, flagged
        return {"status": 0, "error": type(e).__name__}
    og = {}
    for tag in META.findall(body.split("</head>")[0] if "</head>" in body else body):
        key = (attr(tag, "property") or attr(tag, "name")).lower()
        if key in ("og:image", "twitter:image", "og:title", "og:description", "description") and key not in og:
            og[key] = attr(tag, "content")
    image = og.get("og:image") or og.get("twitter:image") or ""
    if image.startswith("//"):
        image = "https:" + image
    elif image.startswith("/"):
        image = re.match(r"https?://[^/]+", final).group(0) + image
    return {"status": status, "final": final if final != url else "", "og_image": image if image.startswith("http") else "",
            "og_title": og.get("og:title", "")[:160], "og_description": (og.get("og:description") or og.get("description") or "")[:240]}


def load(path):
    return [json.loads(l) for l in path.read_text().split("\n") if l.strip()] if path.exists() else []


def web(a):
    base = ROOT / "research" / a.domain
    done = {p["url"] for p in load(base / "probes.jsonl")}
    todo = [r["url"] for r in load(base / "records.jsonl")
            if (a.all or r["url"] not in done) and "youtube.com/watch" not in r["url"] and "x.com/" not in r["url"]]
    todo = list(dict.fromkeys(todo))
    print(f"probing {len(todo)} urls", file=sys.stderr)
    alive = 0
    with open(base / "probes.jsonl", "a", encoding="utf-8") as fh, cf.ThreadPoolExecutor(a.workers) as pool:
        for url, res in zip(todo, pool.map(fetch, todo)):
            res = {"url": url, "at": time.strftime("%Y-%m-%d"), **res}
            alive += 200 <= res["status"] < 400
            fh.write(json.dumps(res, ensure_ascii=False) + "\n")
    print(f"{alive}/{len(todo)} alive", file=sys.stderr)


QUERY = """query { %s }"""
FRAG = """r%d: repository(owner: "%s", name: "%s") { nameWithOwner stargazerCount isArchived pushedAt description
  licenseInfo { spdxId } openGraphImageUrl homepageUrl repositoryTopics(first: 8) { nodes { topic { name } } } }"""


def github(a):
    base = ROOT / "research" / a.domain
    done = {g["github"] for g in load(base / "github.jsonl")}
    repos = sorted({r["github"] for r in load(base / "records.jsonl") if r.get("github") and (a.all or r["github"] not in done)})
    print(f"looking up {len(repos)} repos", file=sys.stderr)
    with open(base / "github.jsonl", "a", encoding="utf-8") as fh:
        for i in range(0, len(repos), 40):
            chunk = repos[i:i + 40]
            q = QUERY % "\n".join(FRAG % (n, *r.split("/", 1)) for n, r in enumerate(chunk) if re.fullmatch(r"[\w.-]+/[\w.-]+", r))
            out = subprocess.run(["gh", "api", "graphql", "-f", f"query={q}"], capture_output=True, text=True)
            data = (json.loads(out.stdout or "{}").get("data") or {})
            for n, repo in enumerate(chunk):
                node = data.get(f"r{n}")
                row = {"github": repo, "at": time.strftime("%Y-%m-%d"), "found": bool(node)}
                if node:
                    row.update({"name": node["nameWithOwner"], "stars": node["stargazerCount"], "archived": node["isArchived"],
                                "pushed": (node["pushedAt"] or "")[:10], "description": (node["description"] or "")[:240],
                                "licence": (node.get("licenseInfo") or {}).get("spdxId") or "", "homepage": node.get("homepageUrl") or "",
                                "topics": [t["topic"]["name"] for t in node["repositoryTopics"]["nodes"]]})
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(f"  {min(i + 40, len(repos))}/{len(repos)}", file=sys.stderr)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("what", choices=["web", "github"])
    p.add_argument("--domain", required=True)
    p.add_argument("--all", action="store_true", help="re-check records already probed")
    p.add_argument("--workers", type=int, default=16)
    a = p.parse_args()
    (web if a.what == "web" else github)(a)


if __name__ == "__main__":
    main()
