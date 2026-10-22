#!/usr/bin/env python3
"""Snapshot registry.directory's item index (every public shadcn registry item) and record each registry.

  python3 research/tools/registry_directory.py

The 11 MB item index is data, so it goes to the data plane as a dated snapshot that `foundry find` searches
(foundry-data/research/ui/registry-directory-items-<date>.json). Git gets one record per registry, rewritten each run
as research/ui/observations/registry-directory.jsonl.
"""
import collections, json, os, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"


def main():
    req = urllib.request.Request("https://registry.directory/items.json", headers={"User-Agent": UA})
    raw = urllib.request.urlopen(req, timeout=120).read()
    items = json.loads(raw)["items"]
    data = Path(os.environ.get("FOUNDRY_DATA", "/Volumes/SISO-STORAGE-VAULT/foundry-data")).expanduser()
    snap = data / "research" / "ui" / f"registry-directory-items-{time.strftime('%Y-%m-%d')}.json"
    snap.parent.mkdir(parents=True, exist_ok=True)
    snap.write_bytes(raw)
    regs = {}
    for it in items:
        r = it["registry"]
        cur = regs.setdefault(r["basePath"], {"name": r["name"], "avatar": r.get("avatarUrl", ""), "types": collections.Counter(),
                                              "cats": collections.Counter()})
        cur["types"][it.get("type", "").replace("registry:", "")] += 1
        cur["cats"].update(it.get("categories") or [])
    out = ROOT / "research" / "ui" / "observations" / "registry-directory.jsonl"
    with open(out, "w", encoding="utf-8") as fh:
        for base, r in sorted(regs.items(), key=lambda x: -sum(x[1]["types"].values())):
            n = sum(r["types"].values())
            fh.write(json.dumps({
                "url": f"https://registry.directory{base}", "title": r["name"], "kind": "registry", "area": "components",
                "source": "https://registry.directory/items.json", "licence": "per registry", "preview": r["avatar"],
                "why": f"{n} items on registry.directory: " + ", ".join(f"{c} {t}" for t, c in r["types"].most_common(4))
                       + (f"; mostly {', '.join(k for k, _ in r['cats'].most_common(3))}" if r["cats"] else "") + ".",
                "tags": ["registry.directory"] + [k for k, _ in r["cats"].most_common(4)], "github": "", "stars": None,
                "free": None, "date": time.strftime("%Y-%m-%d"), "by": r["name"],
            }, ensure_ascii=False) + "\n")
    print(f"{len(items)} items from {len(regs)} registries; snapshot {snap}")


if __name__ == "__main__":
    main()
