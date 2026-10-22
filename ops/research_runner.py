#!/usr/bin/env python3
"""foundry research v2 — the L4 harness at thesis scale.

v1 skimmed repo-card metadata with 5 sequential calls. v2 does what the
GOD-QUESTIONS contract actually says: fan agents over the God-source slice and
READ THE CONTENT — per-repo README evidence extraction in parallel MiniMax
workers, plus cross-domain evidence from the insights corpus (FTS) and creator
transcripts. Then synthesize with citations.

Read-only on all Foundry DBs; writes only ~/foundry-data/research/<slug>/.
Budget guard: --max-calls (default 40), three 429s = abort with partial.
"""
import sqlite3, os, sys, json, time, re, datetime, urllib.request, urllib.error, argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

HOME = os.path.expanduser("~")
DB_IDENT = f"{HOME}/foundry-data/domains/github/identity/identity.sqlite"
DB_INSIGHTS = f"{HOME}/Projects/research-os/insights.db"
DB_QUEUE = f"{HOME}/Projects/youtube-ai-research/database/queue.db"
ENDPOINT = "https://api.minimax.io/anthropic/v1/messages"
MODEL = "MiniMax-M3"
WORKERS = 10                       # categorizer-proven concurrency

def load_key():
    for line in open(f"{HOME}/Projects/youtube-ai-research/.env.local"):
        if line.startswith("MINIMAX_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("no MINIMAX_API_KEY")

KEY = load_key()
_calls = 0
_429s = 0

def minimax(prompt, max_tokens=1600):
    global _calls, _429s
    _calls += 1
    body = json.dumps({"model": MODEL, "max_tokens": max_tokens,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(ENDPOINT, data=body, headers={
        "x-api-key": KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    for _ in range(3):
        try:
            with urllib.request.urlopen(req, timeout=150) as r:
                data = json.loads(r.read())
                return "".join(b.get("text", "") for b in data.get("content", []))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                _429s += 1
                if _429s >= 3:
                    raise RuntimeError("429 wall x3 — aborting per budget guard")
                time.sleep(25); continue
            raise
    raise RuntimeError("retries exhausted")

def ro(path):
    con = sqlite3.connect(path); con.execute("PRAGMA query_only=ON")
    con.row_factory = sqlite3.Row
    return con

def keywords(question):
    stop = {"what", "best", "which", "should", "with", "that", "have", "this", "from",
            "does", "patterns", "there", "over", "into", "your", "ours", "them", "when",
            "most", "make", "give", "giving", "their", "they", "across"}
    return [w for w in re.findall(r"[a-zA-Z]{4,}", question.lower()) if w not in stop][:8]

def phrases(question):
    """2-word phrases from the question (strongest topical signal), e.g. 'code search', 'agent memory'."""
    words = re.findall(r"[a-zA-Z]{3,}", question.lower())
    stop = {"the", "and", "for", "that", "with", "are", "what", "best", "which", "should"}
    out = []
    for i in range(len(words) - 1):
        if words[i] not in stop and words[i+1] not in stop:
            out.append(f"{words[i]} {words[i+1]}")
    return out[:6]

def get_slice(question, category, saucy, limit):
    """Rank by RELEVANCE (phrase hits > keyword hits) first, value second — else the
    saucy/value ordering floats corpus-wide winners that have nothing to do with the question."""
    con = ro(DB_IDENT)
    where, params = ["rc.overall_value IS NOT NULL"], []
    if saucy: where.append("rc.saucy=1")
    score_terms, score_params = [], []
    if category:
        where.append("cat.name LIKE ?"); params.append(f"%{category}%")
    kws, phs = keywords(question), phrases(question)
    for p in phs:   # phrase match = 3 points
        score_terms.append("(CASE WHEN c.description LIKE ? OR rc.why LIKE ? THEN 3 ELSE 0 END)")
        score_params += [f"%{p}%"] * 2
    for k in kws:   # keyword match = 1 point
        score_terms.append("(CASE WHEN c.description LIKE ? OR rc.why LIKE ? OR cat.name LIKE ? OR c.full_name LIKE ? THEN 1 ELSE 0 END)")
        score_params += [f"%{k}%"] * 4
    score = " + ".join(score_terms) if score_terms else "0"
    rows = [dict(r) for r in con.execute(
        f"""SELECT DISTINCT c.full_name, c.stars, c.language, substr(c.description,1,160) AS description,
              cat.name AS category, rc.overall_value, rc.saucy, substr(rc.why,1,160) AS why,
              ({score}) AS rel
            FROM repo_card c JOIN repo_category rc ON rc.full_name=c.full_name
            LEFT JOIN category cat ON cat.id=rc.category_id
            WHERE {' AND '.join(where)} AND ({score}) > 0
            ORDER BY rel DESC, rc.saucy DESC, rc.overall_value DESC, c.stars DESC LIMIT ?""",
        score_params + params + score_params + [limit])]
    con.close()
    return rows

def fetch_readme(full_name, cap=6000):
    """README via raw.githubusercontent HEAD (resolves default branch). Skip on any failure."""
    for fname in ("README.md", "readme.md", "README.rst"):
        try:
            req = urllib.request.Request(
                f"https://raw.githubusercontent.com/{full_name}/HEAD/{fname}",
                headers={"User-Agent": "foundry-research/2"})
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.read(cap * 2).decode("utf-8", "replace")[:cap]
        except Exception:
            continue
    return None

def repo_worker(question, r):
    readme = fetch_readme(r["full_name"])
    src = f"README ({len(readme)} chars)" if readme else "card only (no README fetched)"
    prompt = f"""Evidence extractor. QUESTION: {question}

REPO: {r['full_name']} ({r['stars']}★ {r['language'] or '-'}; category={r['category']}; value={r['overall_value']}{'; SAUCY' if r['saucy'] else ''})
DESCRIPTION: {r['description'] or '-'}
CURATOR NOTE: {r['why'] or '-'}
{'README:' if readme else ''}
{readme or ''}

Return STRICT JSON only:
{{"relevant": true/false,
 "patterns": ["specific technique/pattern this repo evidences for the question, max 3"],
 "evidence": "one concrete fact/quote from the README that supports it",
 "grade": "A|B|C"}}
relevant=false if it does not genuinely bear on the question."""
    try:
        raw = minimax(prompt, max_tokens=700)
        m = re.search(r"\{.*\}", raw, re.S)
        out = json.loads(m.group(0)) if m else {"relevant": False}
    except Exception as e:
        out = {"relevant": False, "error": str(e)[:120]}
    out["repo"] = r["full_name"]
    out["source"] = src
    return out

def insights_evidence(question, limit=12):
    try:
        con = ro(DB_INSIGHTS)
        kws = keywords(question)
        q = " OR ".join(kws[:4]) or question
        rows = [dict(r) for r in con.execute(
            """SELECT source_creator, title, substr(body,1,300) AS body, actionability
               FROM insights WHERE id IN (SELECT rowid FROM insights_fts WHERE insights_fts MATCH ?)
               ORDER BY actionability DESC LIMIT ?""", (q, limit))]
        con.close()
        return rows
    except Exception:
        return []

def transcript_evidence(question, limit=2, cap=7000):
    try:
        con = ro(DB_QUEUE)
        kws = keywords(question)
        like = " OR ".join("title LIKE ?" for _ in kws[:4])
        rows = [dict(r) for r in con.execute(
            f"""SELECT title, channel_name, transcript_path FROM video_queue
                WHERE status='completed' AND transcript_path IS NOT NULL AND ({like})
                ORDER BY upload_date DESC LIMIT ?""",
            [f"%{k}%" for k in kws[:4]] + [limit])]
        con.close()
        out = []
        for r in rows:
            try:
                body = open(r["transcript_path"], encoding="utf-8", errors="replace").read()[:cap]
                out.append({"title": r["title"], "channel": r["channel_name"], "excerpt": body})
            except Exception:
                pass
        return out
    except Exception:
        return []

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("question")
    ap.add_argument("--category", default=None)
    ap.add_argument("--saucy", action="store_true")
    ap.add_argument("--limit", type=int, default=200, help="slice size")
    ap.add_argument("--deep", type=int, default=36, help="repos to deep-read (1 call each)")
    ap.add_argument("--max-calls", type=int, default=40, dest="max_calls")
    a = ap.parse_args()

    t0 = time.time()
    repos = get_slice(a.question, a.category, a.saucy, a.limit)
    if not repos:
        print("NOT FOUND: empty God-source slice"); sys.exit(3)
    deep = repos[:min(a.deep, a.max_calls - 4)]          # reserve calls for cross-domain + synthesis
    print(f"[slice] {len(repos)} repos, deep-reading {len(deep)} in {WORKERS} parallel workers", flush=True)

    ins = insights_evidence(a.question)
    trs = transcript_evidence(a.question)
    print(f"[cross-domain] {len(ins)} insights, {len(trs)} transcripts", flush=True)

    results, done = [], 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(repo_worker, a.question, r): r for r in deep}
        for f in as_completed(futs):
            results.append(f.result()); done += 1
            if done % 10 == 0:
                print(f"[deep-read] {done}/{len(deep)}", flush=True)

    relevant = [r for r in results if r.get("relevant")]
    errored = [r for r in results if r.get("error")]
    print(f"[evidence] {len(relevant)}/{len(results)} repos relevant ({len(errored)} errored), {_calls} calls so far", flush=True)
    # FAIL LOUD on quota wall: a zero-evidence synthesis is worse than no answer.
    if not relevant and len(errored) >= len(results) * 0.5:
        print(f"ABORT: {len(errored)}/{len(results)} workers errored (likely 429 quota wall) — "
              f"no evidence extracted; refusing to synthesize garbage. Sample: {errored[0].get('error','?')}", flush=True)
        sys.exit(4)

    ev = {"repos": relevant,
          "insights": ins,
          "transcripts": [{"title": t["title"], "channel": t["channel"]} for t in trs],
          "shallow_pool": [{"repo": r["full_name"], "why": r["why"]} for r in repos[len(deep):]][:60]}
    ev_txt = json.dumps(ev, indent=0)[:24000]
    tr_txt = "\n\n".join(f"TRANSCRIPT: {t['title']} ({t['channel']})\n{t['excerpt'][:5000]}" for t in trs)[:11000]

    synth = minimax(f"""Synthesize the best-evidence answer a curated corpus can support.
QUESTION: {a.question}

DEEP EVIDENCE ({len(relevant)} repos read at README depth, {len(ins)} mined insights, {len(trs)} creator transcripts):
{ev_txt}

{tr_txt}

Write markdown: (1) direct answer; (2) the strongest patterns, each with repo/insight/transcript citations;
(3) top 5-8 repos to study with one line each on WHY; (4) contrarian/counter-evidence found, if any;
(5) confidence grade A/B/C per major claim + what evidence would raise it.""", max_tokens=3800)

    slug = re.sub(r"[^a-z0-9]+", "-", a.question.lower())[:60].strip("-")
    outdir = f"{HOME}/foundry-data/research/{datetime.date.today().isoformat()}-{slug}"
    os.makedirs(outdir, exist_ok=True)
    json.dump({"question": a.question, "slice": len(repos), "deep": len(deep),
               "calls": _calls, "evidence": ev}, open(f"{outdir}/evidence.json", "w"), indent=1)
    open(f"{outdir}/answer.md", "w").write(
        f"# {a.question}\n\n_foundry research v2 · {datetime.date.today()} · slice={len(repos)} · "
        f"deep-read={len(deep)} READMEs · {len(ins)} insights · {len(trs)} transcripts · "
        f"{_calls} MiniMax calls · {time.time()-t0:.0f}s_\n\n{synth}\n")
    print(f"\n[done] {_calls} calls, {time.time()-t0:.0f}s\n[answer] {outdir}/answer.md\n", flush=True)
    print(synth)

if __name__ == "__main__":
    main()
