# Which speech-to-text model should SISO Voice run locally? (8 Oct 2026)

Evidence: Hugging Face's Open ASR Leaderboard, English short-form, read from the results CSV the leaderboard itself
loads (`research/tools/asr_leaderboard.py`; 63 models, `foundry find --domain voice open-asr-leaderboard`).
WER is the average word error rate across eight test sets (lower is better). RTFx is seconds of audio transcribed
per second of compute on the leaderboard's GPU, so compare RTFx between models, not to a Mac.

## The numbers that decide it

| Model | Avg WER | RTFx | Size | Licence | Languages |
|---|---|---|---|---|---|
| Best API (zoom/scribe_v2_pro) | 3.59% | — | — | proprietary | 11 |
| Qwen/Qwen3-ASR-1.7B | 4.31% (best open) | 820 | 2.0B | Apache-2.0 | 52 |
| CohereLabs/cohere-transcribe-03-2026 | 4.67% | 907 | 2B | Apache-2.0 | 14 |
| nvidia/parakeet-tdt-0.6b-v2 | 4.67% | 14,199 | 0.6B | CC-BY-4.0 | English |
| nvidia/parakeet-tdt-0.6b-v3 | 4.71% | 13,155 | 0.6B | CC-BY-4.0 | 25 |
| ibm-granite/granite-speech-5.0-470m-turboctc | 5.03% | 20,946 | 0.47B | Apache-2.0 | — |
| openai/whisper-large-v3-turbo | 6.36% | 797 | 0.8B | MIT | 99 |
| openai/whisper-large-v3 | 5.78% | 470 | 2B | Apache-2.0 | 99 |

## What it means for SISO Voice

1. **Parakeet TDT 0.6B is the default.** It is within 0.4 points of the best open model and about 16 times faster than
   Qwen3-ASR, at a third of the size. v3 adds 25 European languages for 0.04 points of WER. It runs on Apple Silicon
   through FluidAudio (CoreML), mlx-audio and sherpa-onnx, and Handy and OpenWhispr already ship it.
2. **Whisper is no longer the right default.** Parakeet beats Whisper large-v3 on accuracy (4.7% vs 5.8%) and on
   speed by more than ten times. Keep Whisper only for languages Parakeet lacks.
3. **Qwen3-ASR-1.7B is the accuracy upgrade** for a "high quality" mode or non-European languages (52); it is slower.
4. **The paid APIs are about one point better** (3.6 to 4.3%). That is the gap a cloud mode buys.
5. **Watch the licences:** Parakeet is CC-BY-4.0 (attribution needed); the granite turboctc `-nc` variant and the
   Zipformer models are non-commercial.

## Competitor pricing (8 Oct 2026, read from the pages)

Wispr Flow Pro $15 per user a month (teams $23 to $33). Typeless Pro $12 a month billed yearly, or $30 monthly.
Superwhisper Pro $8.49 a month, free tier with unlimited local Whisper, and a lifetime plan.
A free, local SISO Voice on Parakeet undercuts all three on price; the gap to close is AI cleanup and per-app modes.
