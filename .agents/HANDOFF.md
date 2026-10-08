# HANDOFF: RESEARCH (domain research in the Foundry)

Owner: RESEARCH, Opus on the Mac mini. Branch `research/domains`. Brief: siso-agent-zero `jobs/research-domains/BRIEF.md`,
decision ADR 0006. Updated 2026-10-08 16:35 UTC.

## The lookup (any agent, either machine)

```bash
foundry find <words> [--domain ui|agent-bases|voice] [--area awards] [--kind site] [--json]
foundry frontier [--domain ui]      # leads worth working next
foundry stats                       # records, sources, lookups
```

- Mac mini: `foundry` is on PATH (a link in `~/.local/bin` to this checkout's `bin/foundry`). Works now.
- Laptop: run `bin/foundry` from a Foundry checkout that has this branch. The laptop checkout is on
  `wip-awesome-and-embeddings` with uncommitted edits, so RESEARCH did not touch it; Agent Zero wires PATH there.
- Exit 0 found, 3 nothing found. Lookups are counted in `$FOUNDRY_DATA/usage/find.jsonl` (default
  `~/.local/share/siso-foundry`). Other subcommands (`repos`, `transcripts`, `people`, …) pass through to the
  foundry-corpus skill's CLI, so one name covers both.
- The UI domain search also covers the UI Hub's 1,182 component items when the `banks/siso-ui-hub` checkout sits beside
  the Foundry.

## Pages he can open (Tailscale)

- Index: http://100.66.34.21:8766/
- Award sites with previews: http://100.66.34.21:8766/ui-awards.html (1,441 sites, 1,414 with previews, tag chips)
- Served by `foundry serve --host 100.66.34.21` (mini, started by hand with nohup; it does not survive a reboot).
  Regenerate with `foundry page all`.

## Counts (before → after, 8 Oct)

| Domain | Records | With preview | Sources | Open leads | Rejected |
|---|---|---|---|---|---|
| ui | 0 → 3,403 | 3,239 | 1,610 | 129 | 498 |
| agent-bases | 0 → 1,262 | 1,252 | 95 | 20 | 141 |
| voice | 0 → 116 | 116 | 1 | 0 | 0 |

UI areas: awards 1,441 · components 996 · 3d-motion 456 · image-gen 157 · shells 134 · videos 108 · people 56 · assets 55.
Agent-bases areas: harnesses 517 · skill-hubs 449 · mcp 126 · memory 83 · frameworks 68 · people 19.
Lookups: 0 → 8 on the mini (RESEARCH's own tests; agents have not been told yet).

## Top ten finds

1. Awwwards archive, 1,362 winners with the award's own thumbnail and stack tags (GSAP, Three.js, WebGL), 2011 to today:
   http://100.66.34.21:8766/ui-awards.html
2. Breaking down my Awwwards winning project (Ilja van Eck, Sep 2026): https://www.youtube.com/watch?v=Mc2QP_mJQ2Y
   (preview https://i.ytimg.com/vi/Mc2QP_mJQ2Y/hqdefault.jpg)
3. registry.directory: index of every public shadcn registry with an items.json feed; UI-HUB's next ingest:
   https://registry.directory
4. assistant-ui and Vercel AI Elements: the agent-chat component sets (tool calls, approvals, artifacts) for Agent Base:
   https://www.assistant-ui.com · https://ai-sdk.dev/elements
5. dashboardblocks (239 MIT blocks) and square-ui (Linear-style layouts): shells for operator dashboards:
   https://www.dashboardblocks.com · https://square.lndev.me
6. Poly Haven, ambientCG, Kenney: CC0 HDRIs, PBR textures and models, no attribution: https://polyhaven.com
7. Bruno Simon's WebGPU & TSL course intro (Sep 2026): https://www.youtube.com/watch?v=8HeNnp9sdm4
8. Happy Coder (24k stars, phone control of Claude Code/Codex) and CloudCLI (web UI for agent sessions):
   https://github.com/slopus/happy · https://github.com/siteboon/claudecodeui
9. Nimbalyst: open-source visual workspace running Claude Code, Codex and OpenCode side by side:
   https://github.com/nimbalyst/nimbalyst
10. anthropics/skills and the official plugin directory: the formats SISO's skills hub should match:
    https://github.com/anthropics/skills · https://github.com/anthropics/claude-plugins-official

Licence flags before UI-HUB copies code: coss sits in an AGPL monorepo; React Bits and Animate UI have no plain licence;
GSAP is free but not open source; Vercel AI Chatbot is "Other".

## Frontier, top five

1. Mine which libraries Awwwards winners actually ship (https://www.awwwards.com/websites/three-js/), to rank our 3D stack.
2. Compare generative-UI specs (A2UI, json-render, OpenUI, AG-UI) for agents that emit UI.
3. Ingest registry.directory's items.json: every public shadcn registry item.
4. Sweep GitHub for harness GUIs and pane managers created since June 2026.
5. Codrops case studies and the Awwwards channel's case-study playlists.

## How it works

- `research/<domain>/observations/*.jsonl`: append-only finds, one per line (format in `research/HARVEST.md`).
- `research/<domain>/records.jsonl`: built by `foundry build`; stable ids; deduplicated by GitHub repo, then by
  normalised URL; every source kept.
- Facts from the source: `research/tools/probe.py` (liveness, og:image, GitHub's own stars and licence). A 404 or a
  repo GitHub does not know moves the record to `rejected.jsonl`.
- Judgment: `research/<domain>/curation/*.jsonl` (keep or drop, rank 1 to 5, a sharper why), by RESEARCH's curators.
- Harvesters: `yt_harvest.py` (real YouTube metadata), `awards_harvest.py` (Awwwards archives), `awesome_import.py`
  (other people's lists from the Foundry awesome catalog, mapped in `research/<domain>/lists.json`).
- Data plane: the awesome catalog snapshot is on the vault (`foundry-data/domains/github/awesome/`); generated pages
  and lookup counts are in `~/.local/share/siso-foundry`.

## Traps

- Haiku harvest helpers invented URLs (140 of 150 YouTube ids, 108 GitHub repos, wrong X handles). Every record now
  passes the probe gate; curators verify by fetching. Never accept a helper's file without `probe.py`.
- macOS has no `timeout`; a helper's yt-dlp calls failed silently on it, and the helper invented results instead.
- GitHub rate-limits page fetches (HTTP 429); the web probe skips github.com and uses the API instead.
- `npm test` on main failed on the mini before this branch: a laptop-only run receipt and three committed personal paths.
  Both are fixed here.

## Next

Assets depth (only 55 kept), voice domain beyond the speech-AI list, agent-bases videos and people, more award sources
(CSSDA, FWA, Godly), then the frontier top five.
