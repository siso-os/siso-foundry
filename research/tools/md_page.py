#!/usr/bin/env python3
"""Render a research Markdown file (notes, questions, SYSTEM.md) as a plain HTML page for `foundry serve`.

  python3 research/tools/md_page.py research/SYSTEM.md research-system.html

Handles what research notes use: headings, paragraphs, numbered and bullet lists, pipe tables, bold and code spans.
Writes to $FOUNDRY_DATA/artifacts (default ~/.local/share/siso-foundry/artifacts).
"""
import html, os, re, sys
from pathlib import Path

CSS = ("body{font:16px/1.55 -apple-system,system-ui,sans-serif;max-width:980px;margin:32px auto;padding:0 20px;color:#1a1a1a}"
       "table{border-collapse:collapse;width:100%;margin:12px 0;font-size:14px}td,th{border:1px solid #ddd;padding:8px;"
       "vertical-align:top;text-align:left}th{background:#f4f4f4}code{background:#f2f2f2;padding:1px 4px;border-radius:3px;"
       "font-size:13px}h2{margin-top:36px;border-bottom:1px solid #eee}li{margin:6px 0}")
ITEM = re.compile(r"^(\d+\.|-) ")


def inline(t):
    t = html.escape(t)
    return re.sub(r"`(.+?)`", r"<code>\1</code>", re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t))


def render(lines):
    out, para, i = [], [], 0

    def flush():
        if para:
            out.append("<p>" + inline(" ".join(para)) + "</p>")
            para.clear()
    if lines and lines[0] == "---":  # question frontmatter: shown as a small table
        end = lines.index("---", 1)
        out.append("<table>" + "".join(f"<tr><th>{inline(k)}</th><td>{inline(v.strip())}</td></tr>"
                                       for k, _, v in (l.partition(":") for l in lines[1:end])) + "</table>")
        i = end + 1
    while i < len(lines):
        line = lines[i]
        if line.startswith("|"):
            flush()
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                if not re.match(r"^\|[-| :]+\|$", lines[i]):
                    rows.append([c.strip() for c in lines[i].strip("|").split("|")])
                i += 1
            out.append("<table>" + "".join("<tr>" + "".join(f"<{t}>{inline(c)}</{t}>" for c in r) + "</tr>"
                                            for n, r in enumerate(rows) for t in ["th" if n == 0 else "td"]) + "</table>")
            continue
        m = re.match(r"^(#+) (.*)", line)
        if m:
            flush()
            out.append(f"<h{len(m.group(1))}>{inline(m.group(2))}</h{len(m.group(1))}>")
        elif ITEM.match(line):
            flush()
            tag, items = ("ol" if line[0].isdigit() else "ul"), []
            while i < len(lines) and (ITEM.match(lines[i]) or (lines[i].startswith("   ") and items)):
                if ITEM.match(lines[i]):
                    items.append(ITEM.sub("", lines[i]))
                else:
                    items[-1] += " " + lines[i].strip()
                i += 1
            out.append(f"<{tag}>" + "".join(f"<li>{inline(x)}</li>" for x in items) + f"</{tag}>")
            continue
        elif not line.strip():
            flush()
        else:
            para.append(line.strip())
        i += 1
    flush()
    return out


def main():
    src, name = Path(sys.argv[1]), sys.argv[2]
    lines = src.read_text(encoding="utf-8").split("\n")
    title = next((l[2:] for l in lines if l.startswith("# ")), src.stem)
    dest = Path(os.environ.get("FOUNDRY_DATA", "~/.local/share/siso-foundry")).expanduser() / "artifacts" / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(f"<!doctype html><meta charset=utf-8><title>{html.escape(title)}</title><style>{CSS}</style>\n"
                    + "\n".join(render(lines)), encoding="utf-8")
    print(dest)


if __name__ == "__main__":
    main()
