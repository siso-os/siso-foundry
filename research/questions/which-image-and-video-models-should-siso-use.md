---
question: Which image and video generation models should SISO use for assets?
domain: ui
asked_by: RESEARCH
status: answered
answered: 2026-10-08
recheck: 2026-11-08
sources: research/tools/lmarena.py, LMArena boards 8 Oct 2026
---

## Answer

Hero images and edits: gpt-image-2.5 leads; the best open model, Qwen-Image 2.1, is #19, about 200 Elo behind.
Local or bulk: Qwen-Image 2512 or Z-Image Turbo (Apache-2.0). FLUX.2 klein is non-commercial.
Video: Gemini Omni Flash leads; MiniMax H3 (community licence) is the best open model at #8; Wan 3.0 is API-only.

## Evidence

research/ui/notes/image-models.md; `foundry find lmarena`.

## Unknown

Leaderboards move monthly; prices not compared.
