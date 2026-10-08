---
name: research-helpers-invent-urls
description: Harvest helpers fabricate URLs, video ids and repos; every research record must pass research/tools/probe.py
metadata:
  type: project
---

On 2026-10-08 the first Haiku harvest wave invented 140 of 150 YouTube ids (`watch?v=vid0140`), 108 GitHub repos
(e.g. `react-three/fiber`) and a dozen X handles. Opus curators with fetch checks did not.

**Why:** a helper whose tool fails (macOS has no `timeout`, so its yt-dlp calls died) fills the gap with plausible
text, and a record file looks the same either way.

**How to apply:** mechanical harvests are deterministic scripts in `research/tools/` (yt_harvest, awards_harvest,
awesome_import, sitemap_21st). After any helper writes observations, run `probe.py github` and `probe.py web` before
`foundry build`; build moves 404s and unknown repos to `rejected.jsonl`. Judgment goes to curators that verify by
fetching. See [[research-domains-handoff]].
