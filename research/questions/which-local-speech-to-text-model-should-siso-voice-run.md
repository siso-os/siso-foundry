---
question: Which speech-to-text model should SISO Voice run locally?
domain: voice
asked_by: RESEARCH
status: answered
answered: 2026-10-08
recheck: 2027-01-08
sources: research/tools/asr_leaderboard.py, Open ASR Leaderboard CSV 8 Oct 2026
---

## Answer

Parakeet TDT 0.6B (v3 for 25 languages, v2 English): 4.7% average WER, within 0.4 points of the best open model and 16 times faster.
Qwen3-ASR-1.7B (4.3%, 52 languages) is the accuracy mode. Whisper large-v3 is worse on accuracy (5.8%) and speed.
Paid APIs lead by about one point (3.6%). Parakeet is CC-BY-4.0 (attribution).

## Evidence

research/voice/notes/local-stt.md; `foundry find --domain voice open-asr-leaderboard`.

## Unknown

Leaderboard RTFx is GPU; Apple Silicon speed is not measured here.
