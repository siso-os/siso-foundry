# Harvest method (domain research)

The Foundry maps each domain SISO builds (UI Hub, agent bases, voice) once, so no agent re-searches it. ADR 0006 in
siso-agent-zero is the decision; this file is the method a harvest helper follows.

## Order of work

1. **Other people's lists first.** Awesome lists on GitHub, galleries, directories, award archives, curated threads.
   Harvest them into records before searching yourself.
2. **Then fill the gaps** with web search, `gh search repos`, and `yt-dlp` (metadata only).
3. **Leads are kept, not chased.** A related search or list you saw but did not work goes to the frontier with a reason
   and a rank.

## One find, one line

Helpers append to `research/<domain>/observations/<lane>.jsonl`: one JSON object per line, no prose.

```json
{"url": "https://… the thing itself, not the list it was found in",
 "title": "its name",
 "kind": "library|registry|component|block-library|template|gallery|award|site|asset-library|tool|tutorial|video|channel|person|blog|list|repo|course|article|directory|app|model",
 "area": "the lane's area slug",
 "source": "URL of the list or page it was found in, or websearch:<query>, ytsearch:<query>, gh-search:<query>",
 "licence": "SPDX id or plain words: CC0, MIT, free with attribution, proprietary, unknown",
 "preview": "an image URL that previews it (og:image, gallery thumbnail, https://opengraph.githubassets.com/1/OWNER/REPO), or empty",
 "why": "one specific line on why it matters to SISO",
 "tags": ["3 to 6 lowercase keywords"],
 "github": "owner/repo or empty",
 "stars": null,
 "free": true,
 "date": "YYYY-MM-DD when it was published or awarded, if known, else empty",
 "by": "author, studio or channel, if known, else empty"}
```

Leads go to `research/<domain>/observations/<lane>.frontier.jsonl`:

```json
{"lead": "a search query or URL not yet worked", "why": "reason", "rank": 5, "area": "slug"}
```

`rank` is 1 to 5; 5 is the most valuable to work next.

## Rules

- Records must be real: from a reputable list or a URL you saw resolve. Never invent a URL.
- Keep the licence. Free versus paid matters; a paid item is recorded as reference, never as robbable.
- Never log in, pay, scrape behind a login or paywall, or print secrets. No clones, no large downloads.
- Previews are links in the record. Screenshots and video files live on the data plane, never in Git.

## After a harvest

`bin/foundry build` merges every observation file into `research/<domain>/records.jsonl` (stable ids, deduplicated by
GitHub repo then by normalised URL, every source kept) and `research/<domain>/frontier.jsonl` (ranked leads).
Observation files are append-only evidence; records are rebuilt from them and keep their ids.
