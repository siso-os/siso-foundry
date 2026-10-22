# Can SISO copy it? Licences of the rank-5 UI picks (8 Oct 2026)

Read from each project's own LICENSE file on GitHub. Records carry the result as `licence` plus a tag:
`foundry find licence:no-redistribution` lists the ones that cannot go into SISO's banks.

## Do not vendor into the component bank or a SISO registry

| Project | Licence | What is allowed |
|---|---|---|
| React Bits (DavidHDev/react-bits) | MIT + Commons Clause | Use in any app or site, commercial too. Never sell, sublicense or redistribute the components, alone, bundled or ported. |
| Animate UI (imskyleen/animate-ui) | MIT + Commons Clause | Same: use in products; never redistribute the components in original form. |
| Square UI (ln-dev7/square-ui) | ln-dev UI License | Use in client sites and SaaS. Never republish, never build a UI kit, template set or design system from it, never compete with it. |

Install these per project from the author's own registry, and keep them out of anything SISO publishes as a kit.

## Copy freely (keep the licence file)

- MIT: shadcn/ui, Magic UI, Kibo UI, Dice UI, prompt-kit, ElevenLabs UI, assistant-ui, Tailark blocks, Facade UI,
  dashboardblocks, openstatus data-table-filters, Lenis, Framer Motion, Three.js, R3F, Drei.
- coss ui: MIT, but only `apps/ui` and `apps/origin`; every other folder of the coss monorepo is AGPL-3.0 (LICENSING.md).
- Apache-2.0 (keep NOTICE): Vercel AI Elements, Vercel AI Chatbot, MCP Apps (mid-relicensing from MIT).
- GSAP: free, plugins included, under GreenSock's Standard No-Charge License; not open source. The only bar is using GSAP
  inside a no-code visual animation builder that competes with Webflow, so a SISO visual animation editor must not
  ship GSAP.

Assets: Poly Haven, ambientCG and Kenney are CC0; Fontshare is free for commercial use but CC BY-ND (no modified fonts);
Icônes aggregates icon sets whose licences vary per set, so check the set.
