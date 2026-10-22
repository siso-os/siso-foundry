# What award-winning sites actually ship (8 Oct 2026)

Evidence, not opinion: `research/tools/stack_probe.py` read the homepage and up to six same-site scripts of 2,961
award-winning sites (Awwwards Site of the Day, Month, Year nominees and Developer awards; FWA; CSS Design Awards; Godly;
One Page Love) and matched library signatures left in shipped code. Sites that failed or blocked are left out. A miss can
mean the code sat in a script the probe did not read, so shares are lower bounds. Re-run:
`python3 research/tools/stack_probe.py --report`.

## Share of winners by award year

| Year (sites) | GSAP | ScrollTrigger | Lenis | Three.js | R3F | Vue | Nuxt | Next.js | Webflow | Lottie | Barba |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026 (579) | 52% | 50% | 50% | 24% | 8% | 17% | 14% | 20% | 16% | 17% | 10% |
| 2025 (339) | 67% | 67% | 57% | 23% | 8% | 22% | 18% | 16% | 21% | 25% | 11% |
| 2024 (345) | 62% | 60% | 49% | 24% | — | 22% | 20% | 16% | 14% | 24% | 8% |
| 2023 (313) | 53% | 51% | 31% | 24% | 7% | 17% | 15% | 23% | 14% | 23% | 8% |
| 2022 (310) | 50% | 48% | 8% | 20% | — | 20% | 15% | 15% | 8% | 20% | 8% |
| 2021 (313) | 39% | 33% | — | 21% | 6% | 17% | 13% | 9% | 7% | 15% | 5% |
| 2020 (277) | 42% | 21% | 5% | 20% | — | 16% | 14% | 11% | 4% | 17% | — |

2026 mixes in FWA, CSSDA and gallery picks, which ship slightly less GSAP than Awwwards winners alone (59% on the
Awwwards-only sample of 261).

## What it means for SISO sites

1. **The award stack is GSAP + ScrollTrigger + Lenis.** Half to two thirds of winners ship GSAP, and Lenis went from 5%
   (2020) and 8% (2022) to about half of all winners since 2024. A SISO site kit without both starts behind.
2. **3D is a quarter, not the default.** Three.js sits at 20 to 24% every year since 2020; most winners earn the award with
   scroll, type and transitions. Use 3D where it carries the story.
3. **React Three Fiber is rare on award sites (8%).** Winners mostly write plain Three.js (or OGL) inside the site's
   framework. R3F remains right for React apps (UI-HUB components); for marketing sites, plain Three.js is the norm.
4. **Vue/Nuxt is as common as Next.js** among winners, and Webflow ships about a fifth of them. Studios pick the stack
   their team animates fastest in; the framework is not what wins.
5. **Page transitions are a signature:** Barba.js or Swup on 10 to 14%, plus framework-native transitions not counted.

Common combinations: GSAP + Lenis (117 sites), GSAP + Lenis + Webflow (115), GSAP + Lenis + Nuxt (82),
GSAP + Lenis + Three.js (61). 2026 examples of the full GSAP + Lenis + Three.js stack: otsuka-air.jp (SHIFTBRAIN),
moto-card.com (Properly Studio), 2xa.studio, bleibtgleich.dev (The First The Last), illoca.unseen.co (Unseen Studio),
izanami-official.com (baqemono), darknode.army (Qream).

Look any site up with `foundry find uses:three.js uses:lenis --area awards`.
