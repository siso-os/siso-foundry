#!/usr/bin/env python3
"""L3 momentum: daily (day, full_name, stars, forks, pushed_at) snapshots.
Sources: repos.db (fresh stars, 56k tracked) + identity.sqlite saucy joins.
Writes ONLY momentum.sqlite (this job is its single writer)."""
import sqlite3, os, datetime, sys

HOME = os.path.expanduser("~")
SRC = f"{HOME}/Projects/github-learnings/repos.db"
DST = f"{HOME}/foundry-data/domains/github/momentum.sqlite"
day = datetime.date.today().isoformat()

src = sqlite3.connect(SRC)                     # plain open: WAL+no-shm breaks mode=ro
src.execute("PRAGMA query_only=ON")            # guarantee read-only
cols = {r[1] for r in src.execute("PRAGMA table_info(repos)")}
sel_forks = "forks" if "forks" in cols else "NULL"
sel_pushed = "pushed_at" if "pushed_at" in cols else "NULL"
sel_vel = "star_velocity" if "star_velocity" in cols else "NULL"
rows = src.execute(
    f"SELECT full_name, stars, {sel_forks}, {sel_pushed}, {sel_vel} FROM repos"
).fetchall()
src.close()

dst = sqlite3.connect(DST)
dst.execute("""CREATE TABLE IF NOT EXISTS repo_snapshot(
  day TEXT NOT NULL, full_name TEXT NOT NULL,
  stars INTEGER, forks INTEGER, pushed_at TEXT, star_velocity REAL,
  PRIMARY KEY(day, full_name))""")
dst.executemany(
    "INSERT OR IGNORE INTO repo_snapshot(day,full_name,stars,forks,pushed_at,star_velocity) VALUES (?,?,?,?,?,?)",
    [(day, *r) for r in rows])
dst.commit()
n = dst.execute("SELECT COUNT(*) FROM repo_snapshot WHERE day=?", (day,)).fetchone()[0]
days = dst.execute("SELECT COUNT(DISTINCT day) FROM repo_snapshot").fetchone()[0]
dst.close()
print(f"[{datetime.datetime.now().isoformat(timespec='seconds')}] snapshot {day}: {n} repos ({days} days held)")
