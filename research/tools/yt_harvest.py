#!/usr/bin/env python3
"""Harvest real YouTube video records for a domain from search queries (metadata only, no downloads).

  python3 research/tools/yt_harvest.py --domain ui --area videos --per 25 "three.js website tutorial" "gsap scrolltrigger"
  python3 research/tools/yt_harvest.py --domain ui --area videos --queries-file q.txt
  python3 research/tools/yt_harvest.py --domain ui --area videos --playlist PLxxxx --playlist https://www.youtube.com/channel/UC.../streams

A playlist is the channel owner's own curation, so every episode is kept (any year, no relevance or view gate).

Searches are filtered to this year's uploads, videos only. Each kept video gets its upload date from a
per-video metadata call. Appends to research/<domain>/observations/yt-<area>.jsonl, skipping ids already there.
"""
import argparse, concurrent.futures as cf, json, re, subprocess, sys, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
THIS_YEAR_VIDEOS = "EgQIBRAB"  # YouTube search filter: upload date this year, type video
STOP = {"how", "to", "the", "a", "an", "with", "for", "and", "build", "building", "website", "websites", "tutorial", "2026", "2025", "design", "web", "ui", "page"}
VOCAB = {
    "ui": ["3d", "webgl", "webgpu", "gsap", "animat", "motion", "award", "awwward", "portfolio", "landing", "shader", "r3f", "threej",
           "spline", "framer", "scroll", "component", "shadcn", "tailwind", "designsystem", "interactive", "creative"],
    "agent-bases": ["agent", "claude", "codex", "mcp", "skill", "subagent", "harness", "opencode", "cursor", "llm", "orchestrat"],
    "voice": ["voice", "dictation", "speech", "whisper", "tts", "stt", "transcri", "realtime"],
}


def norm(text):
    return re.sub(r"[^a-z0-9]", "", text.lower())


def relevant(query, title, domain="ui"):
    """Search pads results with whatever is popular; keep a video only if its title names a subject of the query or the domain."""
    t = norm(title)
    stems = [norm(w)[:6] for w in query.split() if w.lower() not in STOP and norm(w)]
    return any(s in t for s in stems + VOCAB.get(domain, []))


def search(query, per):
    url = "https://www.youtube.com/results?" + urllib.parse.urlencode({"search_query": query, "sp": THIS_YEAR_VIDEOS})
    out = subprocess.run(["yt-dlp", "--no-update", "--flat-playlist", "-J", "--playlist-end", str(per), url],
                         capture_output=True, text=True)
    if out.returncode or not out.stdout.strip():
        print(f"search failed: {query}: {out.stderr.strip()[-200:]}", file=sys.stderr)
        return []
    return [e for e in (json.loads(out.stdout).get("entries") or []) if e and e.get("id")]


def playlist(pid):
    url = pid if pid.startswith("http") else f"https://www.youtube.com/playlist?list={pid}"
    out = subprocess.run(["yt-dlp", "--no-update", "--flat-playlist", "-J", url], capture_output=True, text=True)
    if out.returncode or not out.stdout.strip():
        print(f"playlist failed: {pid}: {out.stderr.strip()[-200:]}", file=sys.stderr)
        return "", []
    d = json.loads(out.stdout)
    return d.get("title") or pid, [e for e in (d.get("entries") or []) if e and e.get("id")]


def upload_dates(ids):
    out = subprocess.run(["yt-dlp", "--no-update", "--skip-download", "--ignore-errors", "--print", "%(id)s\t%(upload_date)s",
                          *[f"https://www.youtube.com/watch?v={i}" for i in ids]], capture_output=True, text=True)
    dates = {}
    for line in out.stdout.splitlines():
        vid, _, d = line.partition("\t")
        if len(d) == 8 and d.isdigit():
            dates[vid] = f"{d[:4]}-{d[4:6]}-{d[6:]}"
    return dates


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--domain", required=True)
    p.add_argument("--area", default="videos")
    p.add_argument("--per", type=int, default=25)
    p.add_argument("--min-views", type=int, default=1500)
    p.add_argument("--min-seconds", type=int, default=120)
    p.add_argument("--queries-file")
    p.add_argument("--playlist", action="append", default=[])
    p.add_argument("queries", nargs="*")
    a = p.parse_args()
    queries = list(a.queries)
    if a.queries_file:
        queries += [q.strip() for q in Path(a.queries_file).read_text().splitlines() if q.strip() and not q.startswith("#")]
    out_path = ROOT / "research" / a.domain / "observations" / f"yt-{a.area}.jsonl"
    seen = set()
    if out_path.exists():
        seen = {json.loads(l)["url"].rsplit("=", 1)[-1] for l in out_path.read_text().splitlines() if l.strip()}
    found = {}
    with cf.ThreadPoolExecutor(4) as pool:
        for q, entries in zip(queries, pool.map(lambda q: search(q, a.per), queries)):
            kept = 0
            for e in entries:
                if e["id"] in seen or e["id"] in found:
                    continue
                if not relevant(q, e.get("title") or "", a.domain):
                    continue
                if (e.get("duration") or 0) < a.min_seconds or (e.get("view_count") or 0) < a.min_views:
                    continue
                found[e["id"]] = (q, e, None)
                kept += 1
            print(f"{kept:3d} kept  {q}", file=sys.stderr)
    for pid in a.playlist:
        title, entries = playlist(pid)
        kept = 0
        for e in entries:
            if not e.get("title") or e["id"] in seen or e["id"] in found or (e.get("duration") or a.min_seconds) < a.min_seconds:
                continue
            found[e["id"]] = (f"playlist:{title}", e, pid)
            kept += 1
        print(f"{kept:3d} kept  playlist {title}", file=sys.stderr)
    ids = list(found)
    dates = {}
    with cf.ThreadPoolExecutor(4) as pool:
        for part in pool.map(upload_dates, [ids[i:i + 15] for i in range(0, len(ids), 15)]):
            dates.update(part)
    with open(out_path, "a", encoding="utf-8") as fh:
        for vid, (q, e, pid) in found.items():
            src = (pid if pid.startswith("http") else f"https://www.youtube.com/playlist?list={pid}") if pid else f"ytsearch:{q}"
            label = f"Episode of '{q[9:]}'" if pid else f"Found for '{q}'"
            fh.write(json.dumps({
                "url": f"https://www.youtube.com/watch?v={vid}", "title": e.get("title", ""), "kind": "video", "area": a.area,
                "source": src, "licence": "YouTube standard licence", "preview": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
                "why": f"{label}: {int(e.get('view_count') or 0):,} views, {int((e.get('duration') or 0) // 60)} min.",
                "tags": [t for t in re.findall(r"[a-z0-9.]+", q.lower().removeprefix("playlist:")) if len(t) > 2][:6], "github": "", "stars": None, "free": True,
                "date": dates.get(vid, ""), "by": e.get("channel") or "", "views": e.get("view_count"),
                "channel_url": f"https://www.youtube.com/channel/{e['channel_id']}" if e.get("channel_id") else "",
            }, ensure_ascii=False) + "\n")
    print(f"{len(found)} videos appended to {out_path.relative_to(ROOT)} ({sum(1 for v in found if v in dates)} dated)")


if __name__ == "__main__":
    main()
