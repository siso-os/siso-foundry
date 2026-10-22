# How SISO should do research (RESEARCH's proposal, 8 Oct 2026)

Written after one full pass over three domains (UI, agent bases, voice: 12,437 records, 166 leads closed) and a sweep
of every research job Agent Zero has dispatched and every research store in the workspace.

## What the evidence says

**What worked.**

1. **Scripts against primary sources.** Every trustworthy record came from code reading the source itself: APIs
   (GitHub, claude-plugins.dev, MCP Registry, registry.directory), JSON embedded in pages (LMArena, Awwwards),
   sitemaps (21st.dev), CSVs (Open ASR Leaderboard) and yt-dlp. These are re-runnable, so the research stays fresh.
2. **A probe gate.** Nothing becomes a record until a fetch proves the page exists. It caught 108 invented GitHub repos.
3. **Batch judgment on rows an agent is handed.** Four curator sub-agents judged 1,377 repos in about 2.5 minutes each.
   Their ids were checked mechanically, and none was wrong.
4. **Short decision notes with an evidence table**, for example `notes/local-stt.md` and `notes/licences.md`.

**What failed.**

1. **Haiku as a source of facts.** Helpers asked to "find" things invented 140 of 150 YouTube ids and 108 repos.
2. **Untyped leads.** Of 181 helper-written leads, 48 were generic ("websearch: bootstrap ui kits") and 41 were
   already covered; 77 led anywhere.
3. **Silent job death.** A `codex-run` bug killed four research jobs on 4 Oct (herdr-landscape, herdr-inventory,
   token-tools, spec-audit). Their `.out` files held only the error, and three answers never landed. Board prior-art
   never landed either.
4. **The same question researched three or four times.** Agent Base rivals and harnesses were researched by
   herdr-landscape, harness-rob, harness-deep and then this pass's `rivals.md`, because no agent could ask "has this
   been answered?"
5. **Knowledge split across stores with no shared ids.** UI knowledge sits in four places: Foundry `research/ui`, the
   siso-ui-hub picks, the component bank and `_data/siso-agency/research`. Competitor research sits in three. Two banks
   the skills point at are not on this machine.

## The design: three objects, four gates, three roles

### Objects

| Object | What it is | Where it lives | Lifetime |
|---|---|---|---|
| **Source** | A re-runnable feed: a harvester and its arguments, e.g. "claude-plugins.dev skills", "Awwwards SOTD", "Open ASR Leaderboard" | `research/sources.json`: domain, adapter, args, cadence, owner, last run, yield | Persistent; `foundry refresh` runs the ones that are due |
| **Question** | A decision someone needs answered, e.g. "which local STT model?" | `research/questions/<slug>.md` with frontmatter: asked by, domain, status, answer in at most 8 lines, evidence (which sources, which date), recheck date or trigger | Answered once, rechecked on its date, never re-asked |
| **Record** | One thing in the world (repo, site, model, person, video) | Already built: observations, then records; ids stable | Rebuilt from observations |

Leads stop being free text. A lead is either a Source not yet registered (an adapter plus a target) or a Question not
yet answered. Anything else is refused when it is written.

### Gates (code, not judgment)

1. **Probe gate:** a record must answer a fetch. Already built.
2. **Id gate:** a curator returns verdicts only for ids it was given; extras or gaps fail the batch. Done by hand
   three times this session, so it should be a command.
3. **Quote gate:** when a model extracts facts from a fetched page, every value must appear in the fetched text, or the
   row is dropped. This is the only way Haiku touches facts.
4. **Receipt gate:** a research job is done only when its output file exists and parses (a question file with an
   answer, or observation JSONL). Otherwise it reports FAIL loudly. This would have caught the 4 Oct deaths.

### Roles

- **Opus (one owner per domain):** writes Questions, decides which Sources matter, judges where the cost of being wrong
  is high, samples about 10% of every batch, and writes the notes. Never bulk-fetches inline.
- **Codex (Sol through `codex-run`):** writes new adapters to a contract (input args, output observation JSONL,
  a test that runs it on one page), and runs heavy many-fetch Questions like harness-rob. Its output must pass the
  receipt gate.
- **Haiku (wide and cheap):** only two jobs. (a) Judge batches of rows it is handed (id gate, Opus samples).
  (b) Extract fields from a page it is handed (quote gate). Never "find" or "list what you know".

Most new sources need no new code. The adapters already built cover the common shapes: paginated JSON API,
JSON embedded in a page, sitemap, GitHub search, YouTube search and playlist, awesome lists, page meta probe.

## Persistent research domains across the base

| Domain | Standing questions | Today |
|---|---|---|
| **UI** (components, award sites, motion and 3D, assets, image tools) | What should UI-HUB copy or ship? What do winners use? | Foundry `ui` (10,364) plus UI-HUB, component bank and agency lanes, no shared ids |
| **Agent bases** (harnesses, rivals, skills, plugins, MCP, memory) | What do rivals do that Agent Base lacks? Which skills or MCP servers should we adopt? | Foundry `agent-bases` plus 142k catalogue entries; rival research in 3 other places |
| **Voice** (dictation, STT and TTS models, voice agents) | Which local model? What do competitors charge? | Foundry `voice` (551) |
| **Models and pricing** (LLM coding, image, video, speech leaderboards and prices) | Which model for which job, at what cost? | Nowhere persistent; the `ai-benchmarks` skill plus this pass's LMArena and ASR boards. Should become its own domain because every routing decision depends on it |
| **Industries and clients** (café, dispensary, agency verticals) | What does the best site in this vertical have? Who are the local competitors? | `foundry/intelligence/agency` (17 industries), superapp-forge, siso-sites crawls, dispo docs; none in the Foundry's record form |
| **People** (creators, studios, maintainers) | Who to learn from or hire; whose work to track | Mac mini people graph; studios and people records in each domain |
| **Engineering prior art** (repos, architecture exemplars) | Has someone built this already? | Repo bank (23,778 rated repos), code references, mini corpus |

Competitors are not a separate domain. They are Questions inside each domain ("Agent Base rivals", "dispensary
competitors"), so they land next to the records they cite.

## What to build, in order

1. **`foundry curate emit|ingest`.** Writes uncurated rows to batch files, then takes the verdicts back through the id
   gate. Haiku or Opus curators then become one command each.
2. **`research/sources.json` and `foundry refresh`.** Registers every harvester built so far (about 15) with a cadence,
   so the catalogues and leaderboards stay current without anyone remembering them.
3. **`research/questions/` and `foundry ask`.** `foundry ask "<question>"` searches answered Questions and notes before
   anyone researches. Move the five notes and the Agent Zero research answers (harness-rob, harness-deep, spec-audit)
   into Question files so the rival question is never asked a fourth time.
4. **The quote gate as `foundry extract`.** Fetch a page, hand the text and a field list to Haiku, keep only values
   found verbatim in the text.
5. **Receipt gate in the brief template.** Every research brief names its output file, and the job runner checks it.
   This belongs with codex-run's owner.
6. **One id space for UI.** Feed UI-HUB picks and the component bank through the Foundry's identity (`gh:` or `url:`
   keys) so a lookup finds a thing once with all its sources. Needs UI-HUB's agreement.

**Built 8 Oct (items 1 to 3):** `foundry curate emit|ingest` (id gate tested: an invented id fails the batch and nothing
is written), `research/sources.json` with 21 sources and `foundry refresh [--due|--dry-run]`, and `research/questions/`
with `foundry question new` and `foundry ask`, seeded with six Questions. Built by Codex (Sol) to RESEARCH's spec,
then checked by RESEARCH. Item 4 is next. Items 1 to 4 are inside the Foundry and RESEARCH can build them. Item 5 belongs to codex-run's owner and item 6 to
UI-HUB.
