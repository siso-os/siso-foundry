# HANDOFF: RESEARCH (domain research in the Foundry)

Owner: RESEARCH, Opus on the Mac mini. Branch `research/domains`. Brief: siso-agent-zero `jobs/research-domains/BRIEF.md`,
decision ADR 0006. Updated 2026-10-08 17:35 UTC.

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
  the Foundry, the component bank index, and registry.directory's item snapshot on the vault.

## Pages he can open (Tailscale)

- Index of every domain and area: http://100.66.34.21:8766/
- Award-winning sites with previews: http://100.66.34.21:8766/ui-awards.html (2,919 winners from Awwwards, FWA, CSSDA,
  Godly, One Page Love and galleries, with the award's own thumbnail; filter box and tag chips)
- Award studios, people: http://100.66.34.21:8766/ui-people.html · agent harnesses:
  http://100.66.34.21:8766/agent-bases-harnesses.html · local speech models: http://100.66.34.21:8766/voice-stt.html
- Served by `foundry serve --host 100.66.34.21` (mini, started by hand with nohup; it does not survive a reboot).
  Regenerate with `foundry page all`.

## Counts (8 Oct, end of the second pass)

| Domain | Records | With preview | Sources | Open leads | Rejected |
|---|---|---|---|---|---|
| ui | 10,986 | 10,447 | 3,447 | 0 | 616 |
| agent-bases | 1,426 | 1,402 | 140 | 0 | 730 |
| voice | 551 | 514 | 80 | 0 | 28 |

UI areas: components 5,539 (incl. 3,985 21st.dev items the component bank lacks) · awards 2,919 · 3d-motion 1,382 ·
assets 386 · videos 288 · image-gen 189 · shells 187 · people 96.
`foundry find` also searches item sources beside the records: the UI Hub's items, the component bank index (vault) and
registry.directory's 36,377 shadcn registry items (vault snapshot, area `registry-item`).
Agent-bases areas: harnesses 395 · skill-hubs 366 · videos 355 · mcp 112 · memory 94 · frameworks 84 · people 20.
Voice areas: videos 139 · speech-models 115 · dictation-apps 79 · stt 79 · voice-agents 49 · tts 47 · people 22 · voice-ui 21.
Lookups on the mini: 66, all RESEARCH's own; no other agent has run `foundry find` yet.

## Findings worth his attention

- **Licences (`research/ui/notes/licences.md`):** React Bits and Animate UI are MIT + Commons Clause and Square UI has a
  proprietary licence: all three may be used in sites but never redistributed, so keep them out of SISO's bank and
  registries. coss ui is MIT (only `apps/ui`, `apps/origin`; the rest of coss is AGPL). GSAP is free but bars use inside a
  no-code animation builder. `foundry find licence:no-redistribution`.
- **Local speech-to-text, on numbers (`research/voice/notes/local-stt.md`):** Parakeet TDT 0.6B scores 4.7% WER on the
  Open ASR Leaderboard, 0.4 points behind the best open model (Qwen3-ASR-1.7B, 4.3%) and 16 times faster; Whisper
  large-v3 is worse on both (5.8%). Paid APIs lead by about one point (3.6%). Competitors: Wispr Flow $15/mo, Typeless
  $12/mo yearly, Superwhisper $8.49/mo.
- **Agent Base rivals, by stars:** stablyai/orca (87.8k; fleet of agents in worktrees, mobile companion), getpaseo/paseo
  (20k; one daemon serving desktop, mobile, web, CLI), OrchestratorInc/agent-orchestrator (12.9k; Kanban of workers, PRs,
  CI), akitaonrails/ai-memory (9k; shared memory and claimed handoffs across 20+ agents, closest to .agents/memory), and
  eliasstravik/herdr-projects, a herdr plugin with coordinator, worktree workers and shared memory: almost the Agent
  Base pattern. Commercial: Conductor (parallel worktrees, now cloud), Warp, Amp, Factory, Kiro, Jules, Cursor CLI.
- **What award winners ship (`research/ui/notes/award-stacks.md`, 2,961 sites 2020-2026):** GSAP on half to two thirds,
  Lenis on half since 2024, Three.js a steady quarter, React Three Fiber 8%. The 49 studios with six or more awards
  (Locomotive 50, Immersive Garden 40, Active Theory 32, Obys, Unseen …) are records with their stack: `foundry find studio`.
- **Dictation open source:** besides Handy (MIT, the fork base), OpenWhispr (MIT, 9k, Parakeet built in) and FluidAudio
  (CoreML Parakeet for a native Swift app) are the parts; VoiceInk and FluidVoice are GPL-3.0, so study, don't fork.

## Top ten finds

1. Awwwards archive with previews and stack tags: http://100.66.34.21:8766/ui-awards.html
2. Awwwards' own Live Jury Website Reviews (21 episodes) and Bruno Simon's portfolio devlog: `foundry find jury review`,
   `foundry find bruno simon devlog`
3. stablyai/orca, the biggest open Agent Base rival: https://github.com/stablyai/orca
4. eliasstravik/herdr-projects, a herdr plugin doing coordinator plus worktree workers: https://github.com/eliasstravik/herdr-projects
5. Open ASR Leaderboard as records (WER, speed, licence for 49 open models): `foundry find --domain voice open-asr-leaderboard`
6. Spark, Gaussian splats inside Three.js, and SuperSplat to edit them: https://github.com/sparkjsdev/spark ·
   https://github.com/playcanvas/supersplat
7. Design-system extractors (a site's tokens in one command): design-extract, dembrandt, design-dna
8. assistant-ui and Vercel AI Elements (MIT / Apache-2.0) for Agent Base chat UI: https://www.assistant-ui.com ·
   https://ai-sdk.dev/elements
9. registry.directory, every public shadcn registry item, searchable through `foundry find`
10. anthropics/claude-plugins-community and the official MCP Registry: the formats SISO's hub should match

## Frontier

All three frontiers are worked to zero (166 leads closed with what answered them in `frontier-done.jsonl`). What is
left belongs to other owners or needs a new harvest:

1. Copy the 3,985 21st.dev items into siso-component-bank (UI-HUB / bank owner; list on the vault).
2. Tell agents the lookup exists: no other agent has run `foundry find` yet (Agent Zero).
3. Curate the 1,449 UI awesome-list repos (imported from 21 lists, judged by stars and list only).
4. Turn-detection: no neutral benchmark exists; measure Smart Turn v3 vs LiveKit on SISO's own audio.
5. Re-probe older UI records for previews now that probe.py reads streamed pages (`probe.py web --domain ui --all`).

## How it works

- `research/<domain>/observations/*.jsonl`: append-only finds, one per line (format in `research/HARVEST.md`).
- `research/<domain>/records.jsonl`: built by `foundry build`; stable ids; deduplicated by GitHub repo, then by
  normalised URL; every source kept.
- Facts from the source: `research/tools/probe.py` (liveness, og:image, GitHub's own stars and licence). A 404 or a
  repo GitHub does not know moves the record to `rejected.jsonl`.
- Judgment: `research/<domain>/curation/*.jsonl` (keep or drop, rank 1 to 5, a sharper why), by RESEARCH's curators.
- Harvesters in `research/tools/`: `yt_harvest.py` (real YouTube metadata; `--playlist` for a channel's own
  playlists), `gh_search.py` (GitHub's search API), `asr_leaderboard.py` (Open ASR Leaderboard CSV), `studios.py`
  (award studios from Awwwards profiles), `registry_directory.py`, `delta_21st.py`, `awards_harvest.py` (Awwwards archives),
  `awards_more.py` (FWA, CSSDA, Godly, One Page Love), `codrops_harvest.py` (through camofox on the laptop),
  `sitemap_21st.py`, `stack_probe.py` (libraries winners ship), `awesome_import.py` (other people's lists from the
  Foundry awesome catalog, mapped in `research/<domain>/lists.json`).
- Leads are closed in `research/<domain>/frontier-done.jsonl` with what answered them.
- Data plane: the awesome catalog snapshot is on the vault (`foundry-data/domains/github/awesome/`); generated pages
  and lookup counts are in `~/.local/share/siso-foundry`.

## Traps

- Haiku harvest helpers invented URLs (140 of 150 YouTube ids, 108 GitHub repos, wrong X handles). Every record now
  passes the probe gate; curators verify by fetching. Never accept a helper's file without `probe.py`.
- macOS has no `timeout`; a helper's yt-dlp calls failed silently on it, and the helper invented results instead.
- GitHub rate-limits page fetches (HTTP 429); the web probe skips github.com and uses the API instead.
- 21st.dev and other streamed React pages put a `</head>` inside a script before their meta tags; probe.py now scans the
  whole page. Before that fix every 21st.dev fetch looked empty and the delta harvest silently wrote nothing.
- The record key drops query strings, so records that differ only by `?x=` collapse into one. Give each record a real page.
- `npm test` on main failed on the mini before this branch: a laptop-only run receipt and three committed personal paths.
  Both are fixed here.

## Next

Frontiers are empty; next pass opens new leads rather than working old ones: curate the 1,449 UI awesome-list repos,
re-probe UI previews with `--all`, then a depth pass on the top rivals (orca, paseo, agent-orchestrator) for the
features Agent Base lacks.
