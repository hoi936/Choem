---
name: web-design-guidelines
description: Review UI code for Web Interface Guidelines compliance. Use when asked to "review my UI", "check accessibility", "audit design", "review UX", or "check my site against best practices".
metadata:
  author: vercel
  version: "1.0.0"
  argument-hint: <file-or-pattern>
---

# Web Interface Guidelines

Review files for compliance with Vercel Web Interface Guidelines (Accessibility, Focus States, Forms, Animation, Typography, Content Handling, Images, Performance, Navigation & State, Touch & Interaction, Safe Areas).

## How It Works

1. Read the local guidelines rules in [references/command.md](./references/command.md) (synced from `https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md`).
2. Read the specified HTML/CSS/JS files.
3. Check against all rules in the guidelines:
   - **Accessibility**: Skip link (`<a href="#main-content" class="skip-link">`), semantic HTML, hierarchical `<h1>`–`<h6>`, `aria-label` on icon-only buttons, `aria-live="polite"` on dynamic status/filter counters, `alt` on every `<img>`, `aria-hidden="true"` on decorative SVGs/icons, `scroll-margin-top` on anchored sections.
   - **Focus States**: Explicit `:focus-visible` ring on all interactive controls (`button`, `a`, `input`, `select`, `[tabindex]`). Never `outline: none` without replacement.
   - **Animation**: Explicit transition properties (never `transition: all`), `transform`/`opacity` only, full `@media (prefers-reduced-motion: reduce)` support.
   - **Typography**: `font-variant-numeric: tabular-nums` on numbers/stats/dates, `text-wrap: balance` on headings, proper curly quotes and ellipsis (`…`).
   - **Images**: Explicit `width` and `height` attributes on `<img>` to prevent CLS, `loading="lazy"` on below-the-fold images, `fetchpriority="high"` on hero lead image.
   - **Touch & Interaction**: `touch-action: manipulation`, minimum `44×44px` hit targets on mobile, `overscroll-behavior: contain` on modals/lightboxes, URL hash/query state synchronization.
4. Output findings in `file:line` format and remediate all violations.
