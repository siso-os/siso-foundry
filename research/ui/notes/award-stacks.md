# What award-winning sites actually ship (8 Oct 2026)

Evidence, not opinion: `research/tools/stack_probe.py` read the homepage and up to six same-site scripts of 1,431
award-winning sites (Awwwards Site of the Day, Month, Year nominees and Developer awards, plus the galleries) and
matched library signatures left in shipped code. 1,333 answered; 98 failed or blocked. A miss can mean the code sat in
a script the probe did not read, so shares are lower bounds. Re-run: `python3 research/tools/stack_probe.py --report`.

## Share of winners by award year

| Year (sites) | GSAP | ScrollTrigger | Lenis | Three.js | R3F | Vue | Nuxt | Next.js | Webflow | Lottie | Barba |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026 (261) | 59% | 57% | 59% | 27% | 8% | 21% | 16% | 20% | 19% | 19% | 14% |
| 2025 (338) | 67% | 67% | 57% | 23% | 8% | 21% | 18% | 16% | 21% | 26% | 11% |
| 2024 (334) | 63% | 61% | 51% | 25% | — | 23% | 20% | 15% | 15% | 24% | 9% |
| 2023 (201) | 53% | 51% | 38% | 28% | 8% | 18% | 17% | 21% | 13% | 20% | 9% |

## What it means for SISO sites

1. **The award stack is GSAP + ScrollTrigger + Lenis.** About 60% of winners ship GSAP, and Lenis rose from 38% to 59%
   in three years. A SISO site kit without both starts behind.
2. **3D is a quarter, not the default.** Three.js sits at about 25% every year; most winners earn the award with
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
