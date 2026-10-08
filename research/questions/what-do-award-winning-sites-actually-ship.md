---
question: What libraries do award-winning websites actually ship?
domain: ui
asked_by: RESEARCH
status: answered
answered: 2026-10-08
recheck: 2027-01-08
sources: research/tools/stack_probe.py over 2,961 award winners 2020-2026
---

## Answer

GSAP + ScrollTrigger on half to two thirds of winners; Lenis on about half since 2024; Three.js a steady quarter; React Three Fiber 8%.
Vue/Nuxt is as common as Next.js; Webflow ships about a fifth.

## Evidence

research/ui/notes/award-stacks.md; `foundry find uses:three.js --area awards`.

## Unknown

Shares are lower bounds: only the homepage and six scripts were read.
