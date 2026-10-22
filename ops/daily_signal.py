#!/usr/bin/env python3
"""foundry daily-signal — the organ PUSHES to the harness each morning.
Assembles: heartbeat verdict + momentum top-movers + freshest insights + new research answers
into ~/foundry-data/daily-signal.md. Read from any agent via `foundry signal`. Read-only inputs."""
import sqlite3, os, json, glob, datetime

HOME = os.path.expanduser("~")
today = datetime.date.today()
lines = [f"# Foundry daily signal — {today}", ""]

# 1. heartbeat
try:
    hb = json.load(open(f"{HOME}/foundry-data/heartbeat.json"))
    lines += [f"## Organ health: {hb['overall'].upper()}  ({hb['ts']})"]
    for c in hb["checks"]:
        if c["status"] != "ok":
            lines.append(f"- **{c['status'].upper()}** {c['check']}: {c['detail']}")
    lines.append("")
except Exception as e:
    lines += [f"## Organ health: UNKNOWN ({e})", ""]

# 2. momentum movers (needs >=2 days of snapshots)
try:
    con = sqlite3.connect(f"{HOME}/foundry-data/domains/github/momentum.sqlite")
    con.execute("PRAGMA query_only=ON")
    days = [r[0] for r in con.execute("SELECT DISTINCT day FROM repo_snapshot ORDER BY day DESC LIMIT 2")]
    if len(days) == 2:
        movers = con.execute("""
            SELECT a.full_name, a.stars - b.stars AS delta, a.stars
            FROM repo_snapshot a JOIN repo_snapshot b
              ON a.full_name = b.full_name AND a.day = ? AND b.day = ?
            ORDER BY delta DESC LIMIT 10""", (days[0], days[1])).fetchall()
        lines += [f"## Momentum movers ({days[1]} → {days[0]})"]
        lines += [f"- {m[0]}: +{m[1]}★ (now {m[2]})" for m in movers if m[1] and m[1] > 0] or ["- (no positive movers)"]
    else:
        lines += ["## Momentum movers", f"- history has {len(days)} day(s); movers appear from day 2"]
    con.close(); lines.append("")
except Exception as e:
    lines += ["## Momentum movers", f"- error: {e}", ""]

# 3. freshest insights (last 2 days)
try:
    con = sqlite3.connect(f"{HOME}/Projects/research-os/insights.db")
    con.execute("PRAGMA query_only=ON")
    rows = con.execute("""SELECT source_lane, title, actionability FROM insights
        WHERE last_seen_date >= date('now','-2 day') ORDER BY actionability DESC LIMIT 8""").fetchall()
    lines += ["## Fresh insights (48h)"]
    lines += [f"- [{r[0]}·act{r[2]}] {r[1]}" for r in rows] or ["- none"]
    con.close(); lines.append("")
except Exception as e:
    lines += ["## Fresh insights", f"- error: {e}", ""]

# 4. new research answers (last 3 days)
answers = sorted(glob.glob(f"{HOME}/foundry-data/research/*/answer.md"), key=os.path.getmtime, reverse=True)
recent = [a for a in answers if (datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getmtime(a))).days <= 3]
lines += ["## Research answers (72h)"]
lines += [f"- {a.split('/')[-2]}" for a in recent[:6]] or ["- none"]

open(f"{HOME}/foundry-data/daily-signal.md", "w").write("\n".join(lines) + "\n")
print(f"[{datetime.datetime.now().isoformat(timespec='seconds')}] signal written ({len(lines)} lines)")
