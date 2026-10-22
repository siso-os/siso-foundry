#!/usr/bin/env python3
"""Record the image and video generation models ranked by LMArena's human-vote leaderboards.

  python3 research/tools/lmarena.py [--boards text-to-image,image-edit,text-to-video]

Each public leaderboard page embeds its latest snapshot as JSON (rank, Elo rating, votes, organisation, licence, model
page). One record per model page, carrying its place on every board it appears on. Rewrites
research/ui/observations/lmarena.jsonl and prints the best open-weights model per board.
"""
import argparse, html, json, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"


def entries(board):
    url = f"https://lmarena.ai/leaderboard/{board}"
    page = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60).read().decode()
    s = html.unescape(page).replace('\\"', '"')
    i = s.find('"entries":[')
    if i < 0:
        raise SystemExit(f"{board}: no embedded leaderboard (page layout changed)")
    j = i + len('"entries":')
    depth = 0
    for k in range(j, len(s)):
        depth += {"[": 1, "]": -1}.get(s[k], 0)
        if depth == 0:
            return url, json.loads(s[j:k + 1])


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--boards", default="text-to-image,image-edit,text-to-video")
    a = p.parse_args()
    models = {}
    for board in a.boards.split(","):
        url, rows = entries(board)
        best_open = next((e for e in rows if (e.get("license") or "").lower() != "proprietary"), None)
        print(f"{board}: {len(rows)} models; #1 {rows[0]['modelDisplayName']}; best open "
              + (f"#{best_open['rank']} {best_open['modelDisplayName']} ({best_open.get('license')})" if best_open else "none"))
        for e in rows:
            page = e.get("modelUrl") or ""
            if not page.startswith("http"):
                continue
            m = models.setdefault(page, {"e": e, "boards": [], "source": url})
            m["boards"].append(f"{board} #{e['rank']} of {len(rows)} (Elo {e['rating']:.0f}, {e.get('votes', 0):,} votes)")
    out = ROOT / "research" / "ui" / "observations" / "lmarena.jsonl"
    with open(out, "w", encoding="utf-8") as fh:
        for page, m in models.items():
            e = m["e"]
            lic = e.get("license") or "unknown"
            fh.write(json.dumps({
                "url": page, "title": e["modelDisplayName"], "kind": "model", "area": "image-gen", "source": m["source"],
                "licence": lic, "preview": "", "github": "", "stars": None, "free": lic.lower() != "proprietary",
                "date": time.strftime("%Y-%m-%d"), "by": e.get("modelOrganization") or "",
                "why": f"LMArena human votes: {'; '.join(m['boards'])}. {e.get('modelOrganization') or ''}, {lic}.",
                "tags": ["lmarena", "open-weights" if lic.lower() != "proprietary" else "api"]
                        + [b.split(" #")[0] for b in m["boards"]],
            }, ensure_ascii=False) + "\n")
    print(f"{len(models)} models -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
