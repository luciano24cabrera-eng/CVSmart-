# Glass Visual Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply Aurora/Glassmorphism visual treatment to index.html, aplicar.html, and crear-cv.html while keeping the existing color palette and page structure.

**Architecture:** Add glass CSS variables to theme.css, create a `.glass-card` component and supporting utilities in components.css, then update each HTML page to add background glow divs and switch opaque containers to glass-card. No JS changes required.

**Tech Stack:** Pure HTML/CSS — no build tools, no dependencies beyond existing Google Fonts.

---

## File Map

| File | Change |
|------|--------|
| `frontend/styles/theme.css` | Add 6 glass/glow CSS variables |
| `frontend/styles/components.css` | Add `.glass-card`, `.btn-glass`, update `nav`, `.btn-primary`, `.bg-glows` |
| `frontend/index.html` | Add `.bg-glows`, switch `.card` → `.glass-card`, update hero, stats-grid |
| `frontend/aplicar.html` | Add `.bg-glows`, glass `.form-container`, glass inputs/upload |
| `frontend/crear-cv.html` | Add `.bg-glows`, glass `.cv-form`, glass `.exp-block`/`.edu-block` |

---

## Task 1: Add glass variables to theme.css

**Files:**
- Modify: `frontend/styles/theme.css`

- [ ] **Step 1: Add variables after the existing `--color-shadow-red` line (line 12)**

Open `frontend/styles/theme.css` and add these 6 variables after `--color-shadow-red`:

```css
  /* Glass / Glow */
  --glass-bg: rgba(255, 255, 255, 0.04);
  --glass-border: rgba(255, 255, 255, 0.08);
  --glass-blur: 12px;
  --glass-hover-border: rgba(228, 60, 47, 0.25);
  --glass-hover-shadow: 0 8px 32px rgba(228, 60, 47, 0.12);
  --glow-red-soft: rgba(228, 60, 47, 0.15);
```

- [ ] **Step 2: Verify**

Open `frontend/styles/theme.css` and confirm the 6 new variables appear under `:root` between `--color-shadow-red` and the Typography section.

- [ ] **Step 3: Commit**

```bash
git add frontend/styles/theme.css
git commit -m "feat: add glass and glow CSS variables to theme"
```

---

## Task 2: Add glass components to components.css

**Files:**
- Modify: `frontend/styles/components.css`

- [ ] **Step 1: Make nav always blurred (update lines 4–18)**

Replace the `nav` rule (the non-scrolled state) so it always has blur — not just when `.scrolled`:

```css
nav {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: var(--z-nav);
  background: rgba(10, 10, 10, 0.7);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid rgba(228, 60, 47, 0.1);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--spacing-lg);
  height: 64px;
  transition: background var(--transition-normal), box-shadow var(--transition-normal);
}

nav.scrolled {
  background: rgba(10, 10, 10, 0.85);
  box-shadow: 0 1px 0 rgba(228, 60, 47, 0.15);
}
```

- [ ] **Step 2: Enhance .btn-primary glow**

Replace the `.btn-primary` rule:

```css
.btn-primary {
  background-color: var(--color-accent);
  color: var(--color-text-primary);
  box-shadow: 0 0 24px rgba(228, 60, 47, 0.3);
}

.btn-primary:hover {
  filter: brightness(1.1);
  transform: translateY(-2px);
  box-shadow: 0 0 40px rgba(228, 60, 47, 0.5);
  color: var(--color-text-primary);
}
```

- [ ] **Step 3: Add .btn-glass variant**

Append after the `.btn-tertiary:hover` rule:

```css
.btn-glass {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: var(--color-text-primary);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

.btn-glass:hover {
  background: rgba(255, 255, 255, 0.09);
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-2px);
  color: var(--color-text-primary);
}
```

- [ ] **Step 4: Add .glass-card component**

Replace the existing `.card` rule:

```css
.card {
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-md);
  padding: var(--spacing-lg);
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(228, 60, 47, 0.05) 0%, transparent 60%);
  pointer-events: none;
}

.card:hover {
  border-color: var(--glass-hover-border);
  box-shadow: var(--glass-hover-shadow);
  transform: translateY(-3px);
}
```

- [ ] **Step 5: Add background glows utility**

Append at the end of components.css:

```css
/* BACKGROUND GLOWS */
.bg-glows {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  overflow: hidden;
}

.bg-glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  background: #e43c2f;
}
```

- [ ] **Step 6: Make sure body content is above glows**

Append to components.css:

```css
/* Ensure page content sits above fixed glows */
body > *:not(.bg-glows) {
  position: relative;
  z-index: 1;
}
```

- [ ] **Step 7: Enhance stats-grid with glass**

Replace `.stats-grid` rule:

```css
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0;
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-md);
  overflow: hidden;
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
}
```

- [ ] **Step 8: Verify**

Open `frontend/styles/components.css` and confirm:
- `nav` has `backdrop-filter: blur(16px)` without needing `.scrolled`
- `.card` has `backdrop-filter` and `::before` gradient
- `.btn-glass` exists
- `.bg-glows` and `.bg-glow` exist at the bottom

- [ ] **Step 9: Commit**

```bash
git add frontend/styles/components.css
git commit -m "feat: add glass-card, btn-glass, bg-glows components and enhance nav/btn-primary"
```

---

## Task 3: Update index.html

**Files:**
- Modify: `frontend/index.html`

- [ ] **Step 1: Add background glows div**

After the opening `<body>` tag (before `<nav>`), add:

```html
<div class="bg-glows" aria-hidden="true">
  <div class="bg-glow" style="width:500px;height:500px;opacity:0.14;top:-120px;left:50%;transform:translateX(-50%)"></div>
  <div class="bg-glow" style="width:280px;height:280px;opacity:0.07;bottom:80px;right:-60px"></div>
  <div class="bg-glow" style="width:200px;height:200px;opacity:0.06;top:300px;left:-80px"></div>
</div>
```

- [ ] **Step 2: Add gradient text on hero headline**

In the `<style>` block inside index.html, add after `.hero h1 .accent`:

```css
.hero h1 .gradient-text {
  background: linear-gradient(135deg, #e43c2f, #ff7b6e);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
```

Then in the hero `<h1>`, change `<span class="accent">inteligente</span>` to:

```html
<span class="gradient-text">inteligente</span>
```

- [ ] **Step 3: Open index.html in browser and verify**

Open `frontend/index.html` directly in a browser (or via dev server). Confirm:
- Red glow visible behind hero area (subtle, not overwhelming)
- "inteligente" shows gradient from red to lighter red/pink
- Nav has blur effect (blurs content behind it when scrolling)

- [ ] **Step 4: Commit**

```bash
git add frontend/index.html
git commit -m "feat: add glass glows and gradient text to index.html"
```

---

## Task 4: Update aplicar.html

**Files:**
- Modify: `frontend/aplicar.html`

- [ ] **Step 1: Add background glows**

After the opening `<body>` tag (before `<nav>`), add:

```html
<div class="bg-glows" aria-hidden="true">
  <div class="bg-glow" style="width:400px;height:400px;opacity:0.12;top:-80px;right:-60px"></div>
  <div class="bg-glow" style="width:250px;height:250px;opacity:0.07;bottom:60px;left:-80px"></div>
</div>
```

- [ ] **Step 2: Apply glass to .form-container**

In the `<style>` block inside aplicar.html, replace the `.form-container` rule:

```css
.form-container {
  max-width: 600px;
  margin: 80px auto 3rem;
  padding: 2rem;
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-md);
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  width: 100%;
  position: relative;
  overflow: hidden;
}

.form-container::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(228, 60, 47, 0.04) 0%, transparent 50%);
  pointer-events: none;
}
```

- [ ] **Step 3: Apply glass to form inputs**

In the same `<style>` block, replace the `.form-group input, .form-group textarea, .form-group select` background:

```css
.form-group input,
.form-group textarea,
.form-group select {
  width: 100%;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.05);
  color: var(--color-text-primary);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-sm);
  font-family: var(--font-body);
  font-size: 0.95rem;
  transition: border-color var(--transition-normal), box-shadow var(--transition-normal), background var(--transition-normal);
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
  outline: none;
  border-color: rgba(228, 60, 47, 0.5);
  background: rgba(255, 255, 255, 0.08);
  box-shadow: 0 0 0 3px rgba(228, 60, 47, 0.12);
}
```

- [ ] **Step 4: Apply glass to upload zone**

Replace `.upload-zone`:

```css
.upload-zone {
  border: 1.5px dashed rgba(228, 60, 47, 0.35);
  border-radius: var(--radius-md);
  padding: 2rem;
  text-align: center;
  cursor: pointer;
  transition: all var(--transition-normal);
  background: rgba(228, 60, 47, 0.04);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
}

.upload-zone:hover,
.upload-zone.drag-over {
  border-color: var(--color-accent);
  background: rgba(228, 60, 47, 0.08);
  box-shadow: 0 0 20px rgba(228, 60, 47, 0.08);
}
```

- [ ] **Step 5: Add glow to submit button**

Replace `.form-submit`:

```css
.form-submit {
  width: 100%;
  padding: 14px;
  background-color: var(--color-accent);
  color: var(--color-text-primary);
  border: none;
  border-radius: var(--radius-sm);
  font-weight: var(--fw-semi-bold);
  font-size: 1rem;
  cursor: pointer;
  transition: all var(--transition-normal);
  margin-top: 0.5rem;
  box-shadow: 0 0 24px rgba(228, 60, 47, 0.3);
}

.form-submit:hover {
  box-shadow: 0 0 40px rgba(228, 60, 47, 0.5);
  transform: translateY(-2px);
}
```

- [ ] **Step 6: Open aplicar.html in browser and verify**

Open `frontend/aplicar.html` directly. Confirm:
- Form container has blur/glass effect (not solid dark gray)
- Inputs appear slightly translucent
- Upload zone has dashed red border
- Submit button has red glow

- [ ] **Step 7: Commit**

```bash
git add frontend/aplicar.html
git commit -m "feat: apply glass treatment to aplicar.html form and inputs"
```

---

## Task 5: Update crear-cv.html

**Files:**
- Modify: `frontend/crear-cv.html`

- [ ] **Step 1: Add background glows**

After the opening `<body>` tag (before `<nav>`), add:

```html
<div class="bg-glows" aria-hidden="true">
  <div class="bg-glow" style="width:450px;height:450px;opacity:0.11;top:-100px;right:-80px"></div>
  <div class="bg-glow" style="width:300px;height:300px;opacity:0.07;bottom:100px;left:-100px"></div>
</div>
```

- [ ] **Step 2: Apply glass to .cv-form**

In the `<style>` block inside crear-cv.html, replace `.cv-form`:

```css
.cv-form {
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-md);
  padding: 2rem;
  margin-bottom: 3rem;
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  position: relative;
  overflow: hidden;
}

.cv-form::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(228, 60, 47, 0.04) 0%, transparent 50%);
  pointer-events: none;
  z-index: 0;
}

.cv-form > * {
  position: relative;
  z-index: 1;
}
```

- [ ] **Step 3: Apply glass to form inputs**

Replace `input, select, textarea` rule in crear-cv.html's `<style>`:

```css
input,
select,
textarea {
  width: 100%;
  padding: 11px 14px;
  background: rgba(255, 255, 255, 0.05);
  color: var(--color-text-primary);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-sm);
  font-size: 0.95rem;
  font-family: var(--font-body);
  transition: border-color var(--transition-normal), box-shadow var(--transition-normal), background var(--transition-normal);
}

input:focus,
select:focus,
textarea:focus {
  outline: none;
  border-color: rgba(228, 60, 47, 0.5);
  background: rgba(255, 255, 255, 0.08);
  box-shadow: 0 0 0 3px rgba(228, 60, 47, 0.12);
}
```

- [ ] **Step 4: Apply glass to exp/edu blocks**

Replace `.exp-block, .edu-block`:

```css
.exp-block,
.edu-block {
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: var(--radius-sm);
  padding: 1.25rem;
  margin-bottom: 1rem;
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
}
```

- [ ] **Step 5: Apply glass to tags-input**

Replace `.tags-input`:

```css
.tags-input {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-sm);
  min-height: 48px;
  cursor: text;
  background: rgba(255, 255, 255, 0.05);
  transition: border-color var(--transition-normal);
}

.tags-input:focus-within {
  border-color: rgba(228, 60, 47, 0.5);
  box-shadow: 0 0 0 3px rgba(228, 60, 47, 0.12);
}
```

- [ ] **Step 6: Add glow to primary CV button**

Replace `.cv-btn-primary`:

```css
.cv-btn-primary {
  background-color: var(--color-accent);
  color: var(--color-text-primary);
  box-shadow: 0 0 24px rgba(228, 60, 47, 0.3);
}

.cv-btn-primary:hover {
  box-shadow: 0 0 40px rgba(228, 60, 47, 0.5);
  transform: translateY(-2px);
}
```

- [ ] **Step 7: Apply glass to preview-card**

Replace `.preview-card`:

```css
.preview-card {
  display: none;
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-md);
  padding: 2.5rem;
  margin-top: 2rem;
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
}
```

- [ ] **Step 8: Open crear-cv.html in browser and verify**

Open `frontend/crear-cv.html` directly. Confirm:
- Main form has glass/blur appearance
- Experience and education blocks look like nested glass panels
- Tags input has translucent background
- Generate button has red glow
- Preview card (if visible) matches glass style

- [ ] **Step 9: Commit**

```bash
git add frontend/crear-cv.html
git commit -m "feat: apply glass treatment to crear-cv.html form, blocks, and preview"
```

---

## Task 6: Cross-page verification

- [ ] **Step 1: Open all three pages side by side and check consistency**

Open `index.html`, `aplicar.html`, `crear-cv.html` in separate tabs. Verify:
- Nav blur is consistent across all 3 pages
- Red glow intensity is similar (subtle, not overpowering)
- Glass cards/containers have matching opacity and blur
- Text remains readable on all glass surfaces (white on glass-bg passes contrast)
- No layout shifts vs. original pages (same widths, padding, spacing)

- [ ] **Step 2: Check mobile (resize browser to 375px wide)**

Confirm:
- Glows don't cause horizontal scroll
- Glass cards still visible and legible at mobile widths
- Form in aplicar.html still usable on mobile

- [ ] **Step 3: Final commit**

```bash
git add .
git commit -m "feat: complete glass visual upgrade for index, aplicar, and crear-cv"
```
