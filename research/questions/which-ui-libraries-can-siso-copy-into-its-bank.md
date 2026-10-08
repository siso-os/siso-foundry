---
question: Which UI libraries may SISO copy into its component bank or registry?
domain: ui
asked_by: RESEARCH
status: answered
answered: 2026-10-08
recheck: 2027-04-08
sources: LICENSE files on GitHub, read 8 Oct 2026
---

## Answer

Not React Bits or Animate UI (MIT + Commons Clause) or Square UI (proprietary): use per project, never redistribute.
coss ui is MIT only in apps/ui and apps/origin; the rest of coss is AGPL.
MIT/Apache picks (shadcn/ui, Magic UI, Kibo, Dice UI, prompt-kit, assistant-ui, AI Elements, Tailark …) are fine with the licence kept.
GSAP is free but barred inside a no-code animation builder.

## Evidence

research/ui/notes/licences.md; `foundry find licence:no-redistribution`.

## Unknown

Licences change; recheck before a bank import.
