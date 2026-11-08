---
name: frontend-ai-skills
description: >-
  Production-grade frontend animation, micro-interactions, scroll choreography, and UI component
  patterns. Use when adding purposeful animations, scroll-reveal transitions, counter animations,
  tab crossfades, focus management, and high-craft interactive behaviors to web interfaces.
---

# Frontend AI Skills — Motion, Choreography & Interactive Polish

Use this skill to enrich frontend interfaces with purposeful, compositor-safe animations (`transform`, `opacity`), tactile micro-interactions, and accessible state transitions.

## Detailed References
- **Motion System & Tokens**: [motion-ui.md](./references/motion-ui.md)
- **Frontend Design Direction**: [frontend-design-direction.md](./references/frontend-design-direction.md)
- **Component & State Patterns**: [frontend-patterns.md](./references/frontend-patterns.md)

## Core Motion Rules

1. **Purposeful Motion Only**:
   - Motion must **guide attention**, **communicate state** (tab switch, filter change, modal open/close), or **preserve spatial continuity**.
   - Animate **only `transform` and `opacity`**. Never use `transition: all` or animate `width`, `height`, `top`, `left`.
2. **Motion Tokens**:
   - `--duration-fast: 180ms` (hover, button press, chip toggle)
   - `--duration-normal: 350ms` (tab crossfade, card reveal, modal enter/exit)
   - `--duration-slow: 600ms` (chapter entrance, counter roll-up)
   - `--ease-out-expo: cubic-bezier(0.22, 1, 0.36, 1)`
   - `--ease-sharp: cubic-bezier(0.4, 0, 0.2, 1)`
3. **Micro-Interactions**:
   - **Buttons & Pills**: Subtle `-2px` lift on `:hover`, `scale(0.98)` on `:active`.
   - **Photo Frames**: Smooth `scale(1.03)` image zoom inside `overflow: hidden` frame over `500ms var(--ease-out-expo)`.
   - **Season / Sub-tab Switching**: Crossfade and subtle `translateY(8px -> 0)` entrance when switching seasons (`season_01`..`season_07`) or sub-tabs (`photos`, `posts`, `videos`).
   - **Scroll-Triggered Reveal & Stat Counters**: Use `IntersectionObserver` to reveal editorial sections and animate impact numbers (`135` bài viết, `563` hình ảnh, `7` mùa) once on first viewport entry.
4. **Accessibility (`prefers-reduced-motion`)**:
   - Always check `window.matchMedia('(prefers-reduced-motion: reduce)').matches` in JS and `@media (prefers-reduced-motion: reduce)` in CSS to disable transforms and instant-complete counter animations.

