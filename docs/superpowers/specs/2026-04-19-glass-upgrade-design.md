# CVSmart — Glass Visual Upgrade

**Date:** 2026-04-19
**Scope:** Visual upgrade (no structural changes) for index.html, aplicar.html, crear-cv.html

## Summary

Apply an Aurora/Glassmorphism visual treatment to three pages while keeping the existing color palette (black #0a0a0a, red #e43c2f, white #ffffff) and page structure. The result is a premium dark UI with depth, blur effects, and red glows — distinct from the current flat dark theme.

## Design Decisions

- **Style:** Glass Cards (Opción A) — backdrop-filter blur on containers, red glows behind, rgba borders
- **Colors:** Unchanged — #0a0a0a background, #e43c2f accent, #fff text
- **Fonts:** Unchanged — Poppins (headings), Inter (body)
- **Pages:** index.html, aplicar.html, crear-cv.html only (panel.html excluded)
- **Type of change:** Visual upgrade — same HTML structure, updated CSS treatment

## What Changes

### theme.css
- Add glass card variables: `--glass-bg`, `--glass-border`, `--glass-blur`
- Add glow variables: `--glow-color`, `--glow-opacity`
- Add gradient text utility for red gradient on headings

### components.css
- `.glass-card`: `backdrop-filter: blur(12px)`, `background: rgba(255,255,255,0.04)`, `border: 1px solid rgba(255,255,255,0.08)`, red gradient overlay on `::before`
- `.glass-card:hover`: red border tint, `box-shadow: 0 8px 32px rgba(228,60,47,0.12)`, `translateY(-3px)`
- `nav`: add `backdrop-filter: blur(16px)`, reduce background opacity to 0.6
- `.btn-primary`: add `box-shadow: 0 0 24px rgba(228,60,47,0.35)` glow
- `.btn-glass`: new variant — translucent background, white border
- Inputs: translucent background, glass focus state with red ring
- Upload zone: dashed red border, glass background

### Each HTML page
- Add `.bg-glows` div with 2–3 absolutely-positioned blur circles (red, opacity 0.08–0.18)
- Wrap section content in `.glass-card` where currently using plain cards or boxes
- Add `.hero-badge` pill above hero h1 on index.html
- Add gradient text (`-webkit-background-clip: text`) on key headline words
- Stats strip on index hero: glass container with 3 stats

### animations.css
- No changes needed

## What Does NOT Change
- HTML structure / section order
- Copy / text content
- CSS variable names already in use
- Responsive breakpoints
- Accessibility attributes

## Acceptance Criteria
- Nav has blur backdrop on all 3 pages
- All cards/form containers use glass treatment
- Red glows visible behind hero sections
- Button primary has red box-shadow glow
- Focus states still visible (WCAG AA)
- No layout shifts vs current pages
