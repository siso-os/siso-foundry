# Which image and video model for SISO assets? (8 Oct 2026)

Evidence: LMArena's human-vote leaderboards (blind pairwise votes, Elo), read from the JSON each public page embeds
(`research/tools/lmarena.py`; 114 models; `foundry find lmarena`, `foundry find lmarena open-weights`).

| Board | Leader | Best open-weights model |
|---|---|---|
| Text to image (82 models) | OpenAI gpt-image-2.5, then gpt-image-2, Grok Imagine 2.0, MAI-Image 2.6, Nano Banana 2.1 | Qwen-Image 2.1 at #19 (Elo 1223 vs 1425) |
| Image edit (59) | gpt-image-2.5, gpt-image-2, Grok Imagine 2.0 | Qwen-Image 2.1 at #18 |
| Text to video (48) | Gemini Omni 1.1 Flash, FLUX 3 Video, Grok Imagine Video 1.5, Seedance 2.0 | MiniMax H3 at #8 (community licence) |

What it means:

1. **Hero images and edits: use the API leaders.** The best open image model sits about 200 Elo below gpt-image-2.5;
   for client-facing hero art the paid models win clearly.
2. **Local or bulk generation: Qwen-Image 2.1** (research licence) or Qwen-Image 2512 and Z-Image Turbo (both
   Apache-2.0, #44 and #59) through ComfyUI. FLUX.2 klein is non-commercial: not for client work.
3. **Video loops: one open model is near the top.** MiniMax H3 is #8 of 48 under a community licence (read its terms
   before client use). Wan 3.0 (#6) is API-only; the Apache-2.0 Wan 2.2 A14B is #42, fine for background texture, not
   for hero video.
