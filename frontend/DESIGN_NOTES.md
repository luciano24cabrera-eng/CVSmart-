# CVSmart Frontend Dark Theme Design

## Overview
CVSmart's frontend has been completely redesigned with a professional dark tech aesthetic.

## Design System

### Color Palette
- **Primary Background**: #0a0a0a (Black)
- **Secondary Background**: #1a1a1a (Dark Gray)
- **Accent**: #e43c2f (Red)
- **Text Primary**: #ffffff (White)
- **Text Secondary**: #a0a0a0 (Gray)

### Typography
- **Headings**: Poppins Bold (700-800)
- **Body**: Inter (400-600)
- **Sizes**: Responsive scaling with clamp()

### Spacing System
- Units: xs (0.5rem), sm (1rem), md (1.5rem), lg (2rem), xl (3rem), 2xl (5rem)
- Applied consistently via CSS variables

### Component Library
- **Navigation**: Fixed, dark background with accent hover states
- **Buttons**: Three variants (primary/red, secondary/border, tertiary/gray)
- **Cards**: Dark background with subtle red borders, hover scale effect
- **Step Badges**: Red circles with white numbers
- **Decorative Lines**: Red lines (100% and 20% opacity) for visual "respiros"

## CSS Architecture

### Files
- `styles/theme.css`: 30 CSS variables for colors, typography, spacing, transitions, z-index
- `styles/components.css`: Reusable component styles (nav, buttons, cards)
- `styles/animations.css`: Keyframes, fade-in utilities, stagger effects, smooth scroll

### Responsive Breakpoints
- Mobile: < 640px (single column, hamburger nav)
- Tablet: 640-1024px (two-column grid)
- Desktop: > 1024px (three-column grid, full navigation)

## Animations & Interactions

### Micro-animations
- **Fade-in**: 0.6s ease, triggered by scroll (IntersectionObserver)
- **Button hover**: 2px elevation, shadow, 0.3s ease
- **Card hover**: 1.02x scale, border highlight, shadow, 0.3s ease
- **Focus states**: 3px red outline, 0.3s ease

### Transitions
- Fast: 0.2s
- Normal: 0.3s (default for hover effects)
- Slow: 0.6s (scroll animations)

## Accessibility

### Contrast Ratios
- White on Black: 19.80:1 (WCAG AAA)
- Gray on Black: 7.57:1 (WCAG AA)
- Red on Black: 4.70:1 (WCAG AA)

### Keyboard Navigation
- All interactive elements focus-visible with 3px red outline
- Tab order follows DOM flow
- No focus traps

### Semantic HTML
- Proper heading hierarchy (h1→h2→h3)
- Form labels associated with inputs
- Button elements for clickable actions
- Proper alt text for images

## Pages Redesigned

1. **index.html** - Landing page with hero, how-it-works, benefits, and CTA
2. **aplicar.html** - Candidate CV submission form
3. **crear-cv.html** - AI-powered CV creator
4. **panel.html** - Recruiter dashboard with candidate grid

## Browser Support

Tested and working on:
- Chrome/Brave (latest)
- Firefox (latest)
- Safari (latest)

## Performance

- **CSS Variables**: 30 custom properties for maintainability
- **GPU Acceleration**: Transform/opacity used for animations (no jank)
- **Lazy Loading**: Scroll animations via IntersectionObserver (efficient)
- **File Size**: Optimized CSS architecture (theme.css + components.css + animations.css)

## Design Decisions

1. **Black #0a0a0a**: Maximum tech aesthetic with high contrast and readability
2. **Poppins Bold**: Distinctive typography for brand recognition
3. **Red #e43c2f**: Vibrant but professional accent color
4. **Minimalismo con respiros**: Decorative lines and generous spacing create premium feel
5. **Three CTAs in hero**: Acknowledges all three user paths (upload, create, recruiter)
6. **Consistent transitions**: 0.3s ease for all interactions = predictable feel
7. **Accessible by default**: WCAG AA/AAA contrast and keyboard navigation built-in

## Future Improvements

- Dark mode toggle (for light theme alternative)
- Custom Poppins font weights per context
- Additional decorative patterns for visual depth
- Component variations (button sizes, card styles)
- Animation preferences (prefers-reduced-motion support)

---
Generated: 2026-04-10
Design System Version: 1.0
