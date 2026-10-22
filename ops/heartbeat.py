#!/usr/bin/env python3
"""P0 heartbeat: freshness contracts per pipeline -> ~/foundry-data/heartbeat.json.
Checks ARTIFATCS (max timestamps / mtimes / ports), never exit codes. Read-only."""
import sqlite3, os, json, time, datetime, socket, subprocess

HOME = os.path.expanduser("~")
now = time.time()
checks = []

def add(name, ok_val, detail, warn=False):
    checks.append({"check": name, "status": ("warn" if warn else ("ok" if ok_val else "dead")), "detail": detail})

def age_h(ts): return (now - ts) / 3600

def sql_ro(path, q):
    con = sqlite3.connect(path); con.execute("PRAGMA query_only=ON")
    try: return con.execute(q).fetchone()[0]
    finally: con.close()

def parse_ts(s):
    if not s: return None
    s = str(s).replace("Z", "").replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try: return datetime.datetime.strptime(s[:19 if fmt.endswith("S") else 10], fmt).timestamp()
        except ValueError: pass
    return None

# 1. github categorizer: last repo_category write < 30h
try:
    ts = parse_ts(sql_ro(f"{HOME}/foundry-data/domains/github/identity/identity.sqlite",
                         "SELECT MAX(built_at) FROM repo_category"))
    add("github_categorize", ts and age_h(ts) < 30, f"last write {age_h(ts):.1f}h ago" if ts else "no timestamp")
except Exception as e: add("github_categorize", False, f"error: {e}")

# 2. github discovery: repos.db mtime < 30h
try:
    m = os.path.getmtime(f"{HOME}/Projects/github-learnings/repos.db")
    add("github_discovery", age_h(m) < 30, f"repos.db {age_h(m):.1f}h old")
except Exception as e: add("github_discovery", False, f"error: {e}")

# 3. yt scrape: newest queue row < 30h
try:
    ts = parse_ts(sql_ro(f"{HOME}/Projects/youtube-ai-research/database/queue.db",
                         "SELECT MAX(created_at) FROM video_queue"))
    add("yt_scrape", ts and age_h(ts) < 30, f"newest video {age_h(ts):.1f}h ago" if ts else "no rows")
except Exception as e: add("yt_scrape", False, f"error: {e}")

# 4. yt transcripts: newest completed < 30h
try:
    ts = parse_ts(sql_ro(f"{HOME}/Projects/youtube-ai-research/database/queue.db",
                         "SELECT MAX(updated_at) FROM video_queue WHERE status='completed'"))
    add("yt_transcripts", ts and age_h(ts) < 30, f"last completed {age_h(ts):.1f}h ago" if ts else "none")
except Exception as e: add("yt_transcripts", False, f"error: {e}")

# 5. research ingest: insights last_seen < 50h (date-granular)
try:
    ts = parse_ts(sql_ro(f"{HOME}/Projects/research-os/insights.db",
                         "SELECT MAX(last_seen_date) FROM insights"))
    add("research_ingest", ts and age_h(ts) < 50, f"last insight {age_h(ts)/24:.1f}d ago" if ts else "none")
except Exception as e: add("research_ingest", False, f"error: {e}")

# 6. momentum: today or yesterday snapshot exists
try:
    d = sql_ro(f"{HOME}/foundry-data/domains/github/momentum.sqlite",
               "SELECT MAX(day) FROM repo_snapshot")
    ok = d and (datetime.date.today() - datetime.date.fromisoformat(d)).days <= 1
    add("momentum_snapshot", ok, f"last day {d}")
except Exception as e: add("momentum_snapshot", False, f"error: {e}")

# 7. people graph: mtime < 30d = warn-only contract (manual until 10X P2)
try:
    m = os.path.getmtime(f"{HOME}/foundry-data/domains/people/people.sqlite")
    fresh = age_h(m) < 24 * 30
    add("people_graph", True, f"{age_h(m)/24:.0f}d old (manual build; P2 makes nightly)", warn=not fresh)
except Exception as e: add("people_graph", False, f"error: {e}")

# 8. interface :8900
try:
    s = socket.create_connection(("127.0.0.1", 8900), timeout=3); s.close()
    add("interface_8900", True, "port open")
except Exception: add("interface_8900", False, "port 8900 closed")

# 9. launchd jobs loaded
try:
    out = subprocess.run(["launchctl", "list"], capture_output=True, text=True, timeout=10).stdout
    for job in ("com.siso.foundry-github-categorize", "com.siso.youtube-worker",
                "com.siso.gh.learnings", "com.siso.research.ingest", "com.siso.yt.repend"):
        add(f"loaded:{job.split('.')[-1]}", job in out, "loaded" if job in out else "NOT loaded")
except Exception as e: add("loaded:launchctl", False, f"error: {e}")

# 10. disk
try:
    st = os.statvfs("/System/Volumes/Data")
    free_gb = st.f_bavail * st.f_frsize / 1e9
    add("disk_free", free_gb > 10, f"{free_gb:.0f} GB free")
except Exception as e: add("disk_free", False, f"error: {e}")

dead = [c for c in checks if c["status"] == "dead"]
overall = "red" if dead else ("yellow" if any(c["status"] == "warn" for c in checks) else "green")
out = {"ts": datetime.datetime.now().isoformat(timespec="seconds"),
       "overall": overall, "dead": [c["check"] for c in dead], "checks": checks}
with open(f"{HOME}/foundry-data/heartbeat.json", "w") as f:
    json.dump(out, f, indent=1)
print(f"[{out['ts']}] heartbeat {overall}" + (f" DEAD: {','.join(out['dead'])}" if dead else ""))
