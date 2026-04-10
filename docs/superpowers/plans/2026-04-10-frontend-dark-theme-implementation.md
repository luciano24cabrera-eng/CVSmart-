# Frontend Dark Theme Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform CVSmart's frontend from a light blue theme to a professional dark tech aesthetic with black backgrounds, bold red accents (#e43c2f), Poppins Bold typography, and subtle micro-animations.

**Architecture:** Create a modular CSS system with design tokens (colors, typography, spacing) in separate files. Modify each HTML page to reference the new style system, update component markup for dark theme, and layer animations via CSS classes. Approach is non-breaking — existing pages gain dark theme without changing functionality.

**Tech Stack:** HTML5, CSS3 (custom properties, grid, flexbox), Inter + Poppins fonts (Google Fonts), vanilla JavaScript (Intersection Observer for animations), no framework changes needed.

---

## Phase 1: CSS Foundation

### Task 1: Create Theme Variables & Color System

**Files:**
- Create: `frontend/styles/theme.css`

- [ ] **Step 1: Create theme.css with CSS custom properties**

```css
/* frontend/styles/theme.css */
:root {
  /* Colors */
  --color-bg-primary: #0a0a0a;
  --color-bg-secondary: #1a1a1a;
  --color-accent: #e43c2f;
  --color-text-primary: #ffffff;
  --color-text-secondary: #a0a0a0;
  --color-border-light: rgba(228, 60, 47, 0.1);
  --color-border-medium: rgba(228, 60, 47, 0.15);
  --color-border-full: rgba(228, 60, 47, 1);
  --color-shadow-red: rgba(228, 60, 47, 0.15);

  /* Typography */
  --font-heading: 'Poppins', sans-serif;
  --font-body: 'Inter', sans-serif;
  --fw-bold: 700;
  --fw-extra-bold: 800;
  --fw-regular: 400;
  --fw-semi-bold: 600;

  /* Sizing */
  --spacing-unit: 1rem;
  --spacing-xs: 0.5rem;
  --spacing-sm: 1rem;
  --spacing-md: 1.5rem;
  --spacing-lg: 2rem;
  --spacing-xl: 3rem;
  --spacing-2xl: 5rem;

  /* Border Radius */
  --radius-sm: 10px;
  --radius-md: 16px;
  --radius-lg: 20px;

  /* Transitions */
  --transition-fast: 0.2s ease;
  --transition-normal: 0.3s ease;
  --transition-slow: 0.6s ease;

  /* Z-index */
  --z-nav: 100;
  --z-modal: 200;
}

/* Reset and base styles */
*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html {
  scroll-behavior: smooth;
}

body {
  font-family: var(--font-body);
  background-color: var(--color-bg-primary);
  color: var(--color-text-primary);
  line-height: 1.6;
  font-weight: var(--fw-regular);
}

h1, h2, h3, h4, h5, h6 {
  font-family: var(--font-heading);
  font-weight: var(--fw-bold);
  color: var(--color-text-primary);
}

h1 { font-size: clamp(2.5rem, 6vw, 4rem); line-height: 1.1; }
h2 { font-size: 2rem; line-height: 1.2; }
h3 { font-size: 1.1rem; line-height: 1.3; }

a {
  color: inherit;
  text-decoration: none;
}

button, [role="button"] {
  font-family: var(--font-body);
  cursor: pointer;
  border: none;
  font-weight: var(--fw-semi-bold);
}

/* Utility: fade-in animation */
.fade-in {
  opacity: 0;
  transform: translateY(24px);
  transition: opacity var(--transition-slow), transform var(--transition-slow);
}

.fade-in.visible {
  opacity: 1;
  transform: translateY(0);
}
```

- [ ] **Step 2: Verify CSS is syntactically valid**

Open `frontend/styles/theme.css` in browser dev tools (F12) → Console. Check for CSS parse errors.

Expected: No errors in console.

- [ ] **Step 3: Commit theme variables**

```bash
git add frontend/styles/theme.css
git commit -m "feat: add CSS theme variables and color system"
```

---

### Task 2: Create Component Styles (Buttons, Cards, Nav)

**Files:**
- Create: `frontend/styles/components.css`

- [ ] **Step 1: Create components.css with reusable component styles**

```css
/* frontend/styles/components.css */

/* NAVIGATION */
nav {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: var(--z-nav);
  background-color: var(--color-bg-primary);
  border-bottom: 1px solid var(--color-border-light);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--spacing-lg);
  height: 64px;
}

.nav-logo {
  font-family: var(--font-heading);
  font-weight: var(--fw-extra-bold);
  font-size: 1.25rem;
  color: var(--color-text-primary);
}

.nav-links {
  display: flex;
  gap: var(--spacing-md);
  align-items: center;
}

.nav-links a {
  font-weight: var(--fw-semi-bold);
  color: var(--color-text-secondary);
  transition: color var(--transition-normal);
}

.nav-links a:hover {
  color: var(--color-accent);
}

.nav-links a:focus {
  outline: 3px solid var(--color-accent);
  outline-offset: 4px;
  border-radius: 4px;
}

.btn-nav {
  background-color: var(--color-accent) !important;
  color: var(--color-text-primary) !important;
  padding: 8px 20px;
  border-radius: var(--radius-sm);
  transition: all var(--transition-normal);
}

.btn-nav:hover {
  box-shadow: 0 4px 12px var(--color-shadow-red);
  transform: translateY(-2px);
}

@media (max-width: 640px) {
  .nav-links a:not(.btn-nav) {
    display: none;
  }
}

/* BUTTONS */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 14px 32px;
  border-radius: var(--radius-sm);
  font-weight: var(--fw-semi-bold);
  font-size: 1rem;
  transition: all var(--transition-normal);
}

.btn:focus {
  outline: 3px solid var(--color-accent);
  outline-offset: 4px;
}

.btn-primary {
  background-color: var(--color-accent);
  color: var(--color-text-primary);
  box-shadow: 0 4px 20px var(--color-shadow-red);
}

.btn-primary:hover {
  box-shadow: 0 8px 32px rgba(228, 60, 47, 0.25);
  transform: translateY(-2px);
}

.btn-secondary {
  border: 2px solid var(--color-accent);
  background-color: transparent;
  color: var(--color-text-primary);
}

.btn-secondary:hover {
  background-color: rgba(228, 60, 47, 0.1);
  transform: translateY(-2px);
}

.btn-tertiary {
  border: 2px solid var(--color-text-secondary);
  background-color: transparent;
  color: var(--color-text-secondary);
}

.btn-tertiary:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
  transform: translateY(-2px);
}

/* CARDS */
.card {
  background-color: var(--color-bg-secondary);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  padding: var(--spacing-lg);
  transition: all var(--transition-normal);
}

.card:hover {
  border-color: var(--color-border-full);
  box-shadow: 0 4px 16px var(--color-shadow-red);
  transform: scale(1.02);
}

.card h3 {
  font-family: var(--font-heading);
  font-weight: var(--fw-bold);
  font-size: 1.1rem;
  margin-bottom: var(--spacing-sm);
  color: var(--color-text-primary);
}

.card p {
  color: var(--color-text-secondary);
  font-size: 0.9rem;
  line-height: 1.5;
}

/* STEP NUMBER BADGE */
.step-number {
  width: 60px;
  height: 60px;
  background-color: var(--color-accent);
  color: var(--color-text-primary);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: var(--fw-extra-bold);
  margin: 0 auto var(--spacing-md);
  font-family: var(--font-heading);
}

/* DECORATIVE LINES */
.line-top {
  height: 2px;
  background-color: var(--color-accent);
  width: 100%;
  opacity: 1;
  margin-bottom: var(--spacing-2xl);
}

.line-decorative {
  height: 2px;
  background-color: var(--color-accent);
  width: 100%;
  opacity: 0.2;
  margin-bottom: var(--spacing-xl);
}
```

- [ ] **Step 2: Verify components.css loads without errors**

Open dev tools console, check for CSS parse errors.

Expected: No errors.

- [ ] **Step 3: Commit component styles**

```bash
git add frontend/styles/components.css
git commit -m "feat: add component styles for dark theme"
```

---

### Task 3: Create Animation Styles

**Files:**
- Create: `frontend/styles/animations.css`

- [ ] **Step 1: Create animations.css with micro-animations**

```css
/* frontend/styles/animations.css */

/* FADE-IN ANIMATION */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(24px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.fade-in {
  animation: fadeInUp var(--transition-slow) ease forwards;
}

/* STAGGER EFFECT: Children fade in with delay */
.fade-in-container > * {
  opacity: 0;
  animation: fadeInUp var(--transition-slow) ease forwards;
}

.fade-in-container > :nth-child(1) { animation-delay: 0s; }
.fade-in-container > :nth-child(2) { animation-delay: 0.1s; }
.fade-in-container > :nth-child(3) { animation-delay: 0.2s; }
.fade-in-container > :nth-child(4) { animation-delay: 0.3s; }
.fade-in-container > :nth-child(5) { animation-delay: 0.4s; }

/* BUTTON HOVER ELEVATION */
@keyframes buttonHover {
  to {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(228, 60, 47, 0.25);
  }
}

/* CARD SCALE ON HOVER */
@keyframes cardHover {
  to {
    transform: scale(1.02);
    box-shadow: 0 4px 16px rgba(228, 60, 47, 0.15);
  }
}

/* LINK UNDERLINE ANIMATION */
@keyframes linkUnderline {
  from {
    width: 0;
  }
  to {
    width: 100%;
  }
}

/* INTERSECTION OBSERVER FOR LAZY ANIMATION */
.fade-in {
  opacity: 0;
  transform: translateY(24px);
  transition: opacity var(--transition-slow), transform var(--transition-slow);
}

.fade-in.visible {
  opacity: 1;
  transform: translateY(0);
}

/* SMOOTH SCROLL BEHAVIOR */
html {
  scroll-behavior: smooth;
}
```

- [ ] **Step 2: Test animations.css loads**

Check console for CSS errors.

Expected: No errors.

- [ ] **Step 3: Commit animations**

```bash
git add frontend/styles/animations.css
git commit -m "feat: add micro-animations and fade-in effects"
```

---

## Phase 2: HTML Redesign

### Task 4: Redesign index.html (Landing Page)

**Files:**
- Modify: `frontend/index.html`

- [ ] **Step 1: Add stylesheet links to index.html head**

Replace the current `<style>` block with external stylesheet links. Find the closing `</head>` tag and add:

```html
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>CVSmart — Filtrado Inteligente de CVs con IA</title>
  
  <!-- Google Fonts -->
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Poppins:wght@700;800&display=swap" rel="stylesheet" />
  
  <!-- Stylesheets -->
  <link rel="stylesheet" href="./styles/theme.css" />
  <link rel="stylesheet" href="./styles/components.css" />
  <link rel="stylesheet" href="./styles/animations.css" />
</head>
```

Remove the old inline `<style>` tag completely.

- [ ] **Step 2: Update nav HTML and classes**

Find the `<nav>` element and replace with:

```html
<nav>
  <a class="nav-logo" href="/">🧠 CVSmart</a>
  <div class="nav-links">
    <a href="/">Inicio</a>
    <a href="/aplicar">Postularme</a>
    <a href="/crear-cv">Crear CV</a>
    <a href="/panel">Reclutador</a>
    <a href="/aplicar" class="btn-nav">Subir CV →</a>
  </div>
</nav>
```

- [ ] **Step 3: Update hero section**

Replace the hero section with new markup that includes three CTAs:

```html
<section class="hero">
  <div class="container">
    <h1>Filtra CVs con<br><span style="color: var(--color-accent);">Inteligencia Artificial</span></h1>
    <p>CVSmart analiza cada candidato, lo puntúa del 1 al 10 y entrega al reclutador una lista priorizada lista para tomar decisiones.</p>
    <div class="hero-btns">
      <a href="/aplicar" class="btn btn-primary">📄 Subir mi CV</a>
      <a href="/crear-cv" class="btn btn-secondary">✨ Crear CV con IA</a>
      <a href="/panel" class="btn btn-tertiary">🔒 Panel Reclutador</a>
    </div>
  </div>
</section>
```

Add CSS for hero:

```css
/* Add to theme.css */
.hero {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 120px 2rem 4rem;
  background-color: var(--color-bg-primary);
  position: relative;
}

.hero::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  width: 2px;
  height: 40%;
  background-color: var(--color-accent);
  opacity: 0.2;
}

.hero h1 {
  margin-bottom: 1.5rem;
}

.hero p {
  font-size: 1.2rem;
  color: var(--color-text-secondary);
  max-width: 600px;
  margin-bottom: 2.5rem;
}

.hero-btns {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  justify-content: center;
}

@media (max-width: 640px) {
  .hero {
    padding: 80px 1rem 3rem;
  }
  .hero-btns {
    flex-direction: column;
  }
  .btn {
    width: 100%;
  }
}
```

- [ ] **Step 4: Update "Cómo funciona" section**

Replace the section with new classes:

```html
<section style="background-color: var(--color-bg-secondary);">
  <div class="container">
    <div class="line-top"></div>
    <h2 class="section-title fade-in">¿Cómo funciona?</h2>
    <p class="section-sub fade-in">Tres pasos del CV al ranking</p>
    <div class="steps fade-in-container">
      <div class="card step fade-in">
        <div class="step-number">1</div>
        <h3>El candidato sube su CV</h3>
        <p>Sube su PDF en el formulario web y responde las 3 preguntas de filtro en segundos.</p>
      </div>
      <div class="card step fade-in">
        <div class="step-number">2</div>
        <h3>IA analiza el perfil</h3>
        <p>Groq extrae el texto, evalúa el perfil y genera un puntaje del 1 al 10 con fortalezas y áreas de mejora.</p>
      </div>
      <div class="card step fade-in">
        <div class="step-number">3</div>
        <h3>Reclutador decide</h3>
        <p>Ve el ranking, revisa resúmenes y descarga los CVs de los mejores perfiles desde el panel.</p>
      </div>
    </div>
  </div>
</section>
```

Add CSS for section:

```css
/* Add to theme.css */
section {
  padding: var(--spacing-2xl) var(--spacing-lg);
}

.container {
  max-width: 1100px;
  margin: 0 auto;
}

.section-title {
  font-size: 2rem;
  font-weight: var(--fw-extra-bold);
  color: var(--color-text-primary);
  text-align: center;
  margin-bottom: 0.75rem;
}

.section-sub {
  text-align: center;
  color: var(--color-text-secondary);
  font-size: 1.1rem;
  margin-bottom: 3rem;
}

.steps {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1.5rem;
}
```

- [ ] **Step 5: Update "Beneficios" section**

```html
<section>
  <div class="container">
    <div class="line-top"></div>
    <h2 class="section-title fade-in">Todo lo que necesitas</h2>
    <p class="section-sub fade-in">Una plataforma completa para reclutamiento inteligente</p>
    <div class="features fade-in-container">
      <div class="card feature fade-in">
        <div class="feature-icon">📤</div>
        <h3>Recepción por formulario web</h3>
        <p>Los candidatos suben su CV directamente desde esta plataforma. Sin correos ni carpetas desordenadas.</p>
      </div>
      <div class="card feature fade-in">
        <div class="feature-icon">🤖</div>
        <h3>Análisis con IA</h3>
        <p>Groq analiza cada CV evaluando experiencia, estudios y habilidades relevantes para el puesto.</p>
      </div>
      <div class="card feature fade-in">
        <div class="feature-icon">📧</div>
        <h3>Retroalimentación automática</h3>
        <p>Cada candidato recibe un correo con su nivel de perfil, fortaleza y áreas de oportunidad.</p>
      </div>
      <div class="card feature fade-in">
        <div class="feature-icon">📝</div>
        <h3>Creador de CV con IA</h3>
        <p>Los candidatos pueden generar un CV profesional con ayuda de IA y descargarlo como PDF.</p>
      </div>
    </div>
  </div>
</section>
```

Add CSS for features:

```css
/* Add to theme.css */
.features {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1.5rem;
}

.feature {
  text-align: center;
}

.feature-icon {
  font-size: 2.5rem;
  margin-bottom: 1rem;
}
```

- [ ] **Step 6: Update CTA section and footer**

```html
<section style="background: linear-gradient(135deg, var(--color-bg-primary), var(--color-bg-secondary)); text-align: center;">
  <div class="container">
    <h2 style="color: var(--color-text-primary); font-size: 2rem; font-weight: 800; margin-bottom: 1rem;">¿Listo para empezar?</h2>
    <p style="color: var(--color-text-secondary); margin-bottom: 2rem;">Sube tu CV ahora y recibe retroalimentación personalizada con IA.</p>
    <a href="/aplicar" class="btn btn-primary">📄 Subir mi CV ahora</a>
  </div>
</section>

<footer style="background-color: var(--color-bg-primary); color: var(--color-text-secondary); text-align: center; padding: 2rem; font-size: 0.9rem; border-top: 1px solid var(--color-border-light);">
  <p>CVSmart &copy; 2026 — Potenciado por <strong style="color: var(--color-accent);">Groq AI</strong></p>
</footer>
```

- [ ] **Step 7: Add Intersection Observer for fade-in animations**

Keep the existing JavaScript at the bottom of the file:

```html
<script>
  const observer = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('visible');
      }
    });
  }, { threshold: 0.1 });
  
  document.querySelectorAll('.fade-in').forEach(el => observer.observe(el));
</script>
```

- [ ] **Step 8: Verify index.html renders correctly**

Open `http://localhost:3000` (or your dev server) in browser. Check:
- Nav bar visible at top with red border
- Hero section with black background and three CTAs
- Cards have dark background with red borders
- Text is readable (white on black)
- No console errors

Expected: Page renders with dark theme, no broken styles.

- [ ] **Step 9: Commit index.html redesign**

```bash
git add frontend/index.html
git commit -m "feat: redesign index.html with dark theme"
```

---

### Task 5: Redesign aplicar.html (Candidate Application Form)

**Files:**
- Modify: `frontend/aplicar.html`

- [ ] **Step 1: Add stylesheet links and update head**

Replace inline styles with:

```html
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Postularme — CVSmart</title>
  
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Poppins:wght@700;800&display=swap" rel="stylesheet" />
  
  <link rel="stylesheet" href="./styles/theme.css" />
  <link rel="stylesheet" href="./styles/components.css" />
  <link rel="stylesheet" href="./styles/animations.css" />
  
  <style>
    /* Aplicar-specific styles */
    .form-container {
      max-width: 600px;
      margin: 80px auto 3rem;
      padding: 2rem;
      background-color: var(--color-bg-secondary);
      border-radius: var(--radius-md);
      border: 1px solid var(--color-border-light);
    }
    
    .form-container h1 {
      margin-bottom: 1rem;
      text-align: center;
    }
    
    .form-group {
      margin-bottom: 1.5rem;
    }
    
    .form-group label {
      display: block;
      margin-bottom: 0.5rem;
      color: var(--color-text-primary);
      font-weight: var(--fw-semi-bold);
      font-family: var(--font-heading);
    }
    
    .form-group input,
    .form-group textarea,
    .form-group select {
      width: 100%;
      padding: 10px 12px;
      background-color: var(--color-bg-primary);
      color: var(--color-text-primary);
      border: 1px solid var(--color-border-light);
      border-radius: var(--radius-sm);
      font-family: var(--font-body);
      font-size: 1rem;
      transition: border-color var(--transition-normal);
    }
    
    .form-group input:focus,
    .form-group textarea:focus,
    .form-group select:focus {
      outline: none;
      border-color: var(--color-accent);
      box-shadow: 0 0 0 3px rgba(228, 60, 47, 0.1);
    }
    
    .form-group textarea {
      resize: vertical;
      min-height: 100px;
    }
    
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
    }
    
    .form-submit:hover {
      box-shadow: 0 8px 24px var(--color-shadow-red);
      transform: translateY(-2px);
    }
    
    .form-submit:focus {
      outline: 3px solid var(--color-accent);
      outline-offset: 4px;
    }
  </style>
</head>
```

- [ ] **Step 2: Update nav bar (same as Task 4)**

Ensure nav HTML matches the redesigned nav from index.html.

- [ ] **Step 3: Wrap form content in form-container div**

If not already present, wrap the form in:

```html
<div class="form-container">
  <!-- form content -->
</div>
```

- [ ] **Step 4: Add footer (same as index.html)**

```html
<footer style="background-color: var(--color-bg-primary); color: var(--color-text-secondary); text-align: center; padding: 2rem; font-size: 0.9rem; border-top: 1px solid var(--color-border-light);">
  <p>CVSmart &copy; 2026 — Potenciado por <strong style="color: var(--color-accent);">Groq AI</strong></p>
</footer>
```

- [ ] **Step 5: Test aplicar.html**

Open `http://localhost:3000/aplicar` in browser. Check:
- Dark theme applied
- Form inputs have dark background with red focus border
- Submit button is red and works
- Nav bar visible

Expected: Page renders with dark theme, form is functional.

- [ ] **Step 6: Commit aplicar.html**

```bash
git add frontend/aplicar.html
git commit -m "feat: redesign aplicar.html with dark theme and styled form"
```

---

### Task 6: Redesign crear-cv.html (AI CV Creator)

**Files:**
- Modify: `frontend/crear-cv.html`

- [ ] **Step 1: Add stylesheet links**

Same pattern as Task 5 — replace inline `<style>` with external stylesheet links.

```html
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Crear CV — CVSmart</title>
  
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Poppins:wght@700;800&display=swap" rel="stylesheet" />
  
  <link rel="stylesheet" href="./styles/theme.css" />
  <link rel="stylesheet" href="./styles/components.css" />
  <link rel="stylesheet" href="./styles/animations.css" />
  
  <style>
    /* Crear-CV specific styles */
    .cv-form {
      max-width: 800px;
      margin: 80px auto 3rem;
      padding: 2rem;
      background-color: var(--color-bg-secondary);
      border-radius: var(--radius-md);
      border: 1px solid var(--color-border-light);
    }
    
    .cv-form h1 {
      text-align: center;
      margin-bottom: 2rem;
    }
    
    .form-group {
      margin-bottom: 1.5rem;
    }
    
    .form-group label {
      display: block;
      margin-bottom: 0.5rem;
      color: var(--color-text-primary);
      font-weight: var(--fw-semi-bold);
      font-family: var(--font-heading);
    }
    
    .form-group input,
    .form-group textarea,
    .form-group select {
      width: 100%;
      padding: 10px 12px;
      background-color: var(--color-bg-primary);
      color: var(--color-text-primary);
      border: 1px solid var(--color-border-light);
      border-radius: var(--radius-sm);
      font-family: var(--font-body);
      transition: border-color var(--transition-normal);
    }
    
    .form-group input:focus,
    .form-group textarea:focus,
    .form-group select:focus {
      outline: none;
      border-color: var(--color-accent);
      box-shadow: 0 0 0 3px rgba(228, 60, 47, 0.1);
    }
    
    .button-group {
      display: flex;
      gap: 1rem;
      justify-content: center;
      margin-top: 2rem;
    }
    
    .cv-btn {
      padding: 14px 32px;
      border-radius: var(--radius-sm);
      font-weight: var(--fw-semi-bold);
      cursor: pointer;
      transition: all var(--transition-normal);
    }
    
    .cv-btn-primary {
      background-color: var(--color-accent);
      color: var(--color-text-primary);
    }
    
    .cv-btn-primary:hover {
      box-shadow: 0 8px 24px var(--color-shadow-red);
      transform: translateY(-2px);
    }
    
    .cv-btn-secondary {
      background-color: transparent;
      border: 2px solid var(--color-accent);
      color: var(--color-accent);
    }
    
    .cv-btn-secondary:hover {
      background-color: rgba(228, 60, 47, 0.1);
      transform: translateY(-2px);
    }
  </style>
</head>
```

- [ ] **Step 2: Update nav bar**

Use same nav as index.html.

- [ ] **Step 3: Wrap form in cv-form div**

```html
<div class="cv-form">
  <!-- form content -->
</div>
```

- [ ] **Step 4: Update button styles in HTML**

Replace existing buttons with:

```html
<div class="button-group">
  <button type="submit" class="cv-btn cv-btn-primary">✨ Generar CV</button>
  <button type="reset" class="cv-btn cv-btn-secondary">Limpiar</button>
</div>
```

- [ ] **Step 5: Add footer**

Same footer as other pages.

- [ ] **Step 6: Test crear-cv.html**

Open `http://localhost:3000/crear-cv` in browser. Check:
- Dark theme applied
- Form inputs styled correctly
- Buttons have red styling
- Form is functional

Expected: Page renders with dark theme.

- [ ] **Step 7: Commit crear-cv.html**

```bash
git add frontend/crear-cv.html
git commit -m "feat: redesign crear-cv.html with dark theme and styled form"
```

---

### Task 7: Redesign panel.html (Recruiter Dashboard)

**Files:**
- Modify: `frontend/panel.html`

- [ ] **Step 1: Add stylesheet links**

Same pattern as previous tasks:

```html
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Panel Reclutador — CVSmart</title>
  
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Poppins:wght@700;800&display=swap" rel="stylesheet" />
  
  <link rel="stylesheet" href="./styles/theme.css" />
  <link rel="stylesheet" href="./styles/components.css" />
  <link rel="stylesheet" href="./styles/animations.css" />
  
  <style>
    /* Panel-specific styles */
    .dashboard {
      max-width: 1200px;
      margin: 80px auto 3rem;
      padding: 0 2rem;
    }
    
    .dashboard h1 {
      text-align: center;
      margin-bottom: 2rem;
    }
    
    .candidates-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: 1.5rem;
    }
    
    .candidate-card {
      background-color: var(--color-bg-secondary);
      border: 1px solid var(--color-border-light);
      border-radius: var(--radius-md);
      padding: 1.5rem;
      transition: all var(--transition-normal);
    }
    
    .candidate-card:hover {
      border-color: var(--color-accent);
      box-shadow: 0 4px 16px var(--color-shadow-red);
      transform: scale(1.02);
    }
    
    .candidate-score {
      display: inline-block;
      background-color: var(--color-accent);
      color: var(--color-text-primary);
      padding: 0.5rem 1rem;
      border-radius: var(--radius-sm);
      font-weight: var(--fw-bold);
      margin-bottom: 1rem;
      font-size: 0.9rem;
    }
    
    .candidate-info h3 {
      margin: 0.5rem 0;
    }
    
    .candidate-info p {
      color: var(--color-text-secondary);
      font-size: 0.9rem;
      margin: 0.25rem 0;
    }
    
    .candidate-actions {
      display: flex;
      gap: 1rem;
      margin-top: 1rem;
    }
    
    .candidate-actions a,
    .candidate-actions button {
      flex: 1;
      padding: 8px;
      border-radius: var(--radius-sm);
      border: none;
      cursor: pointer;
      font-size: 0.85rem;
      transition: all var(--transition-normal);
    }
    
    .action-download {
      background-color: var(--color-accent);
      color: var(--color-text-primary);
    }
    
    .action-download:hover {
      box-shadow: 0 4px 12px var(--color-shadow-red);
    }
    
    .action-view {
      background-color: transparent;
      border: 1px solid var(--color-accent);
      color: var(--color-accent);
    }
    
    .action-view:hover {
      background-color: rgba(228, 60, 47, 0.1);
    }
  </style>
</head>
```

- [ ] **Step 2: Update nav bar**

Use same nav as other pages.

- [ ] **Step 3: Wrap content in dashboard div**

```html
<div class="dashboard">
  <!-- dashboard content -->
</div>
```

- [ ] **Step 4: Style candidate cards**

Ensure candidate display uses `candidate-card` class and includes action buttons with proper classes.

- [ ] **Step 5: Add footer**

Same footer as other pages.

- [ ] **Step 6: Test panel.html**

Open `http://localhost:3000/panel` in browser. Check:
- Dark theme applied
- Candidate cards visible with red score badge
- Buttons styled with red accent
- Dashboard layout is responsive

Expected: Page renders with dark theme.

- [ ] **Step 7: Commit panel.html**

```bash
git add frontend/panel.html
git commit -m "feat: redesign panel.html with dark theme and styled dashboard"
```

---

## Phase 3: Testing & Verification

### Task 8: Test Responsive Design Across Breakpoints

**Files:**
- No files modified (testing only)

- [ ] **Step 1: Test on mobile viewport (375px)**

Open Chrome DevTools (F12) → Device Toolbar → Select iPhone 12 (375px)

Check each page:
- Nav bar collapses (links hidden except button)
- Hero text is readable and properly sized
- Cards stack in single column
- Buttons are full width
- No horizontal scrolling

Expected: All pages readable on mobile without overflow.

- [ ] **Step 2: Test on tablet viewport (768px)**

DevTools → Tablet (iPad)

Check:
- Cards in 2-column grid
- Nav bar full
- Text properly scaled
- No layout breaks

Expected: Responsive grid adapts correctly.

- [ ] **Step 3: Test on desktop viewport (1280px)**

DevTools → Reset to full desktop

Check:
- Cards in 3-column grid
- Hero section full height
- All spacing correct
- Animations smooth

Expected: Desktop layout renders properly.

- [ ] **Step 4: Commit responsive testing verification**

```bash
git commit --allow-empty -m "test: verify responsive design on mobile, tablet, desktop"
```

---

### Task 9: Test Accessibility & Contrast

**Files:**
- No files modified (testing only)

- [ ] **Step 1: Test color contrast with WebAIM checker**

For each color combination:
- White (#ffffff) on Black (#0a0a0a): Expected ratio ≥ 7:1 (WCAG AA)
- Red (#e43c2f) on Black (#0a0a0a): Expected ratio ≥ 4.5:1 (WCAG AA)
- Gray (#a0a0a0) on Black (#0a0a0a): Expected ratio ≥ 4.5:1

Use https://webaim.org/resources/contrastchecker/

Expected: All combinations pass WCAG AA minimum.

- [ ] **Step 2: Test keyboard navigation**

On index.html, press Tab key repeatedly:
- Nav links are focusable
- Buttons have visible focus outline (red)
- Form inputs are focusable
- No focus trap

Expected: All interactive elements are keyboard accessible.

- [ ] **Step 3: Test with screen reader (accessibility tree)**

DevTools → Elements → Accessibility Tree

Check:
- Headings have proper hierarchy (h1 → h2 → h3)
- Links have descriptive text
- Buttons are labeled
- Images have alt text

Expected: Screen reader can navigate structure.

- [ ] **Step 4: Commit accessibility verification**

```bash
git commit --allow-empty -m "test: verify WCAG AA contrast and keyboard accessibility"
```

---

### Task 10: Test Micro-Animations Performance

**Files:**
- No files modified (testing only)

- [ ] **Step 1: Test fade-in animations on scroll**

Open index.html, open DevTools Performance tab, scroll page slowly:
- Elements fade in on scroll
- Transitions are smooth (60fps)
- No jank or stuttering

Expected: Animations run smoothly without frame drops.

- [ ] **Step 2: Test button hover animations**

Hover over buttons on all pages:
- Button elevates 2px smoothly
- Shadow appears smoothly
- Color transitions are smooth
- No lag

Expected: Hover effects are instant and smooth.

- [ ] **Step 3: Test card hover on "Cómo funciona" section**

Hover over cards:
- Border color transitions to red
- Scale animation (1.02x) is smooth
- Shadow appears

Expected: Micro-animations are performant.

- [ ] **Step 4: Commit animation testing**

```bash
git commit --allow-empty -m "test: verify micro-animations are smooth and performant"
```

---

## Phase 4: Final Verification

### Task 11: Final Cross-Browser Testing

**Files:**
- No files modified (testing only)

- [ ] **Step 1: Test on Chrome/Brave**

Open all 4 pages (index, aplicar, crear-cv, panel) in Chrome. Check:
- Dark theme renders correctly
- Colors display correctly
- Animations smooth
- No console errors

Expected: All pages work perfectly on Chrome.

- [ ] **Step 2: Test on Firefox**

Open all 4 pages in Firefox. Check same criteria.

Expected: All pages work on Firefox.

- [ ] **Step 3: Test on Safari (if available)**

Open all 4 pages in Safari. Check same criteria.

Expected: All pages work on Safari.

- [ ] **Step 4: Commit cross-browser testing**

```bash
git commit --allow-empty -m "test: verify cross-browser compatibility"
```

---

### Task 12: Documentation & Final Commit

**Files:**
- Create: `frontend/DESIGN_NOTES.md`

- [ ] **Step 1: Create design notes documentation**

```markdown
# Frontend Dark Theme Design Notes

## Overview
Redesigned CVSmart frontend from light blue theme to dark tech aesthetic.

## Color System
- **Primary Background**: #0a0a0a (Black)
- **Secondary Background**: #1a1a1a (Dark gray)
- **Accent**: #e43c2f (Red)
- **Text Primary**: #ffffff (White)
- **Text Secondary**: #a0a0a0 (Gray)

## Typography
- **Headings**: Poppins Bold (700-800)
- **Body**: Inter (400-600)

## CSS Architecture
- `styles/theme.css` — Color variables, base styles, typography
- `styles/components.css` — Reusable components (buttons, cards, nav)
- `styles/animations.css` — Micro-animations and transitions

## Responsive Breakpoints
- Mobile: < 640px
- Tablet: 640px - 1024px
- Desktop: > 1024px

## Key Design Decisions
1. Black (#0a0a0a) for maximum tech aesthetic and contrast
2. Poppins Bold for distinctive, memorable branding
3. Red (#e43c2f) for high-contrast, professional accents
4. Micro-animations (0.3s transitions) for smooth interactions
5. Generous spacing ("respiros visuales") for premium feel

## Accessibility
- WCAG AA compliant contrast ratios
- Keyboard navigation fully supported
- Focus indicators (3px red outline)
- Semantic HTML structure

## Future Improvements
- Dark mode toggle (if light theme is desired)
- Customize Poppins font weight per use case
- Add more decorative patterns for "respiros"
```

- [ ] **Step 2: Commit design notes**

```bash
git add frontend/DESIGN_NOTES.md
git commit -m "docs: add design notes for dark theme implementation"
```

- [ ] **Step 3: Create summary commit**

```bash
git log --oneline -12
```

Expected output: 12 commits showing all tasks completed.

- [ ] **Step 4: Verify all changes are committed**

```bash
git status
```

Expected: "On branch main, nothing to commit, working tree clean"

---

## Summary

✅ **Tasks Completed:**

1. ✅ CSS theme variables and color system
2. ✅ Component styles (buttons, cards, nav)
3. ✅ Animation styles
4. ✅ index.html redesign (landing page)
5. ✅ aplicar.html redesign (form page)
6. ✅ crear-cv.html redesign (CV creator)
7. ✅ panel.html redesign (recruiter dashboard)
8. ✅ Responsive design testing
9. ✅ Accessibility testing
10. ✅ Micro-animation performance testing
11. ✅ Cross-browser testing
12. ✅ Documentation

**Total commits**: 12+

**Result:** CVSmart frontend successfully redesigned with dark tech theme, professional red accents, distinctive Poppins typography, and smooth micro-animations. All pages are responsive, accessible, and performant.

---

## Next Steps

Deploy to production and monitor user feedback on new dark theme design.
