#!/usr/bin/env python3
"""Record every model on Hugging Face's Open ASR Leaderboard (English short-form) with its measured WER and speed.

  python3 research/tools/asr_leaderboard.py

Reads the results CSV the leaderboard space itself loads (the pinned revision in the space's init.py), keeps the best
row per model, and rewrites research/voice/observations/open-asr.jsonl with the open-weights models (API-only models have
no page of their own to key a record on; they are printed, and their rank still counts). Lower WER is better; RTFx is how many seconds
of audio the model transcribes per second of compute.
"""
import csv, io, json, re, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPACE = "https://huggingface.co/spaces/hf-audio/open_asr_leaderboard"


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "siso-foundry"}), timeout=60).read().decode()


def main():
    init = get(f"{SPACE}/raw/main/init.py")
    m = re.search(r'"english_short":\s*\{"repo":\s*"([^"]+)",\s*"file":\s*"([^"]+)",\s*"revision":\s*"([^"]+)"', init)
    repo, file, rev = m.groups()
    src = f"https://huggingface.co/datasets/{repo}/resolve/{rev}/{file}"
    rows = [r for r in csv.DictReader(io.StringIO(get(src))) if r.get("avg")]
    best = {}
    for r in rows:
        base = r["model"].split(" (")[0].strip()
        if base not in best or float(r["avg"]) < float(best[base]["avg"]):
            best[base] = r
    ranked = sorted(best.items(), key=lambda kv: float(kv[1]["avg"]))
    out = ROOT / "research" / "voice" / "observations" / "open-asr.jsonl"
    with open(out, "w", encoding="utf-8") as fh:
        for i, (model, r) in enumerate(ranked, 1):
            api = r["License"].lower() == "proprietary"
            if api:
                print(f"  API #{i}: {model} {float(r['avg']):.2f}%")
                continue
            wer, rtfx = float(r["avg"]), r.get("RTFx") or ""
            size = r.get("Size (B)") or ""
            fh.write(json.dumps({
                "url": f"https://huggingface.co/{model}", "title": model, "kind": "model", "area": "stt", "source": src,
                "licence": r["License"], "preview": "", "github": "", "stars": None, "free": True,
                "date": time.strftime("%Y-%m-%d"), "by": model.split("/")[0],
                "why": (f"Open ASR Leaderboard, English: {wer:.2f}% average WER, #{i} of {len(ranked)}"
                        + (f"; RTFx {float(rtfx):,.0f}" if rtfx else "") + (f"; {size}B params" if size else "")
                        + (f"; {r['# Languages']} languages" if r.get("# Languages") else "") + f"; {r['License']}."),
                "tags": ["open-asr-leaderboard", "open-weights", r["License"].lower()],
                "wer": round(wer, 2), "rtfx": float(rtfx) if rtfx else None, "leaderboard_rank": i,
            }, ensure_ascii=False) + "\n")
    print(f"{sum(r['License'].lower() != 'proprietary' for _, r in ranked)} open models of {len(ranked)} -> {out.relative_to(ROOT)} (revision {rev[:8]})")


if __name__ == "__main__":
    main()
