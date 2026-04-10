# Frontend Redesign: Dark Tech Theme for CVSmart

**Date**: 2026-04-10  
**Status**: Design Approved  
**Scope**: Complete visual redesign of landing page and public-facing frontend

---

## Overview

Redesign CVSmart's frontend from a light blue theme to a **dark, tech-forward aesthetic** with black backgrounds, bold red accents, and modern typography. The goal is to create a professional, original, and user-friendly interface that feels premium and distinctive.

**Core values**: Professional, Modern, Minimalista con respiros, Original, Tech-forward

---

## Color Palette

| Element | Hex | Usage |
|---------|-----|-------|
| **Background Primary** | `#0a0a0a` | Main page background, nav, footer |
| **Background Secondary** | `#1a1a1a` | Cards, alternate sections, depth |
| **Accent (Primary CTA)** | `#e43c2f` | Buttons, highlights, interactive elements |
| **Text Primary** | `#ffffff` | Headlines, main text |
| **Text Secondary** | `#a0a0a0` | Descriptions, labels, subtle text |
| **Border/Decorative** | `#e43c2f @ 10-20% opacity` | Subtle lines, separators |

**Color combinations:**
- Red accent at 100% opacity: CTAs, hover states
- Red at 20% opacity: decorative lines, subtle highlights
- Red at 5% opacity: background gradients
- Generous use of black for air and elegance

---

## Typography System

| Element | Font | Weight | Size | Usage |
|---------|------|--------|------|-------|
| **H1 (Hero)** | Poppins | 800 | clamp(2.5rem, 6vw, 4rem) | Main headline |
| **H2 (Section Title)** | Poppins | 700 | 2rem | Section headings |
| **H3 (Card Title)** | Poppins | 700 | 1.1rem | Card/step titles |
| **Body** | Inter | 400-600 | 1rem | Paragraph text |
| **Small** | Inter | 400 | 0.9rem | Labels, captions |

**Font strategy:**
- Poppins Bold gives distinctive character — recognizable as "CVSmart"
- Inter provides clean, readable body text
- High contrast for readability on dark backgrounds

---

## Component Architecture

### Navigation Bar
- **Background**: Black `#0a0a0a` with subtle red border bottom (1px, 10% opacity)
- **Height**: 64px, fixed position
- **Logo**: Poppins Bold, white, size 1.25rem
- **Links**: Gray `#a0a0a0`, hover → red `#e43c2f` (0.3s transition)
- **CTA Button** ("Subir CV →"): Red background, white text, hover with subtle shadow
- **Mobile**: Logo + hamburger menu, links hidden until expanded

### Hero Section
- **Background**: Black `#0a0a0a` with decorative red line (2px, 20% opacity) on left side
- **Headline**: Poppins Bold, white, responsive scaling
- **Subheadline**: Inter regular, gray `#a0a0a0`
- **Three CTAs** (equal prominence):
  1. **"📄 Subir mi CV"** — Solid red background, white text, primary action
  2. **"✨ Crear CV con IA"** — Red border, transparent background, secondary action
  3. **"🔒 Panel Reclutador"** — Gray border, tertiary action
- **Interactions**: Buttons elevate 2px on hover, color transitions smooth (0.3s)
- **Spacing**: Generous padding (120px top, 2rem sides), centered content

### Content Cards (How It Works / Benefits)
- **Background**: Grayish-black `#1a1a1a`
- **Border**: Red `#e43c2f` @ 15% opacity (1px), 100% on hover
- **Border radius**: 16px
- **Padding**: 2rem
- **Number badge**: Circle background red, white text, Poppins Bold
- **Hover state**: 
  - Border opacity → 100%
  - Shadow: `0 4px 16px rgba(228, 60, 47, 0.15)`
  - Scale: 1.02x
  - Transition: 0.3s ease
- **Grid**: 3 columns desktop, 2 tablet, 1 mobile

### Section Dividers
- Red line (2px, 100% opacity) above each main section
- Creates visual "respiros" without clutter

### Call-to-Action Section (Bottom)
- **Background**: Black `#0a0a0a` with subtle red gradient (5% opacity, left-to-right)
- **Text**: Centered, Poppins Bold for headline, white
- **Button**: Solid red, large, hover with shadow

### Footer
- **Background**: Black `#0a0a0a` with red top border (2px)
- **Text**: Gray `#a0a0a0`, Poppins for brand name, Inter for body
- **Links**: Gray → red on hover (0.3s)
- **Content**: Minimal, brand + attribution

---

## Animation & Micro-interactions

### Page Load & Scroll
- **Fade-in elements**: Opacity 0 → 1, translateY +24px → 0 (0.6s ease)
- **Trigger**: Intersection Observer, threshold 0.1
- **Elements**: Cards, headings, content blocks

### Hover States (All Interactive Elements)
- **Links**: Color transition red (0.3s), optional subtle underline
- **Buttons**: 
  - Scale: 1.00 → 1.02
  - Shadow: `0 8px 24px rgba(228, 60, 47, 0.2)`
  - Transition: 0.3s ease
- **Cards**: 
  - Scale: 1.00 → 1.02
  - Border color: opacity 15% → 100%
  - Shadow appears
  - Transition: 0.3s ease

### Focus States (Keyboard Navigation)
- Visible red outline on all interactive elements
- Meets WCAG AA accessibility standards

### General Principles
- All transitions: 0.3s ease or faster
- No janky animations, everything smooth
- Subtle shadows using red for depth
- Micro-interactions enhance, don't distract

---

## Layout & Responsive Design

### Breakpoints
- **Mobile**: < 640px
- **Tablet**: 640px - 1024px
- **Desktop**: > 1024px

### Responsive Behavior
- **Hero**: 
  - Desktop: Full height, large headline
  - Mobile: 80vh, headline scales with `clamp()`
- **Cards Grid**:
  - Desktop: 3 columns, gap 1.5rem
  - Tablet: 2 columns, gap 1.5rem
  - Mobile: 1 column, full width with padding
- **Navigation**:
  - Desktop: Full links visible
  - Mobile: Hamburger menu, links in dropdown
- **Typography**:
  - Responsive sizing with `clamp()` for headings
  - Maintains readability across all screen sizes

### Spacing System
- Base unit: 1rem = 16px
- Padding sections: 5rem vertical, 2rem horizontal
- Card padding: 2rem
- Gap between cards: 1.5rem
- Gap between CTAs: 1rem

---

## Accessibility & Contrast

- **Contrast**: White text on black background (21:1 ratio) — exceeds WCAG AAA
- **Red on black**: Red `#e43c2f` on black `#0a0a0a` (7.2:1 ratio) — WCAG AA
- **Focus indicators**: Visible red outline on all interactive elements (min 3px)
- **Font sizing**: Readable at minimum 16px body text
- **Alt text**: All images and icons have descriptive alt text
- **Semantic HTML**: Proper heading hierarchy (H1 → H2 → H3)
- **Keyboard navigation**: All interactive elements accessible via Tab

---

## Files & Structure

```
frontend/
├── index.html           (Redesigned landing page)
├── aplicar.html         (Apply CV page - update colors/typography)
├── crear-cv.html        (Create CV page - update colors/typography)
├── panel.html           (Recruiter dashboard - update colors/typography)
└── styles/
    └── main.css         (Consolidated styles with new color palette)
```

**Implementation approach:**
- Update inline styles in each HTML file with new color variables
- Create CSS custom properties (--color-primary, --color-accent, etc.)
- Ensure consistency across all pages

---

## Key Design Decisions

1. **Black `#0a0a0a` over `#1a1a1a`**: More dramatic, tech-forward look. Reduces eye strain for dark theme users.

2. **Poppins Bold for headings**: Distinctive and memorable. Creates immediate brand recognition. Sets CVSmart apart from generic fintech/HR SaaS.

3. **Red accent (#e43c2f)**: Vibrant but professional. High contrast against black. Draws attention to CTAs without being aggressive.

4. **Minimalismo con respiros**: Decorative lines and cards create visual interest without clutter. Generous spacing feels premium.

5. **Three CTAs in hero**: Acknowledges all three user paths (upload CV, create CV, recruiter login). Equal visual weight.

6. **Subtle gradients (5% opacity)**: Adds depth without overwhelming. Maintains minimalist aesthetic.

---

## Success Criteria

- [ ] All pages successfully redesigned to dark theme
- [ ] Typography hierarchy clear (Poppins for headers, Inter for body)
- [ ] Red accent used consistently across CTAs, hover states, borders
- [ ] Micro-animations smooth and performant (60fps)
- [ ] Responsive design tested on mobile (375px), tablet (768px), desktop (1280px)
- [ ] Accessibility: WCAG AA compliance, keyboard navigation working
- [ ] Brand recognition: "Tech-forward, professional, original" when viewed
- [ ] User feedback: Improved satisfaction vs. current blue theme

---

## Out of Scope

- Backend changes
- Functionality additions
- Other pages beyond landing & public-facing UI
- Database modifications

---

## Next Steps

1. ✅ Brainstorm & design approval (this document)
2. → Write implementation plan (writing-plans skill)
3. → Execute implementation
4. → Test on all devices
5. → Deploy to production
