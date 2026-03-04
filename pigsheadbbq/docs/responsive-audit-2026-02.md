# Responsive Design Audit (Pigs Head BBQ)

Date: 2026-02-28
Auditor: Senior frontend review (AI)
Scope: `index.html`, `about.html`, `styles/main.css`, `scripts/main.js`

## Method

- Reviewed responsive CSS/layout rules in `styles/main.css` and page structure in `index.html` + `about.html`.
- Ran viewport checks at: **320, 375, 390, 414, 768, 1024, 1280, 1440**.
- Captured full-page screenshots for each target breakpoint.
- Spot-checked mobile nav behavior and responsive embeds.

## Top 10 improvements (highest impact first)

1. **Problem:** Large, fixed-height third-party embeds (`Facebook iframe` at 680px high; menu iframe with tall minimum heights) dominate small screens.  
   **Why it matters:** On 320–414px devices, key content is pushed far below the fold and users scroll excessively before reaching CTAs/forms.  
   **Suggested fix:** Use fluid heights with `clamp()` and viewport-relative units (`min-height: clamp(300px, 55svh, 680px)`) and allow user expansion ("Open fullscreen").  
   **Estimated effort:** S  
   **Risk:** Low

2. **Problem:** Mobile nav panel lacks explicit dismiss affordances beyond menu button/link click and has no Escape-key handling/focus return.  
   **Why it matters:** Keyboard and assistive-tech users can get a suboptimal navigation loop; interaction quality drops on tablet/mobile widths where hamburger is default up to 940px.  
   **Suggested fix:** Add Escape-to-close, outside-click close for nav drawer, and focus management (move focus into first item when opened; return to toggle when closed).  
   **Estimated effort:** M  
   **Risk:** Low

3. **Problem:** Focus-visible styling is limited to `a` and `button`; form controls and checkbox rely on browser defaults.  
   **Why it matters:** Responsive layouts increase keyboard/touch usage; inconsistent focus visibility harms accessibility and perceived quality.  
   **Suggested fix:** Extend focus styles to `input`, `select`, `textarea`, and custom checkbox states using `:focus-visible` and clear contrast tokens.  
   **Estimated effort:** S  
   **Risk:** Low

4. **Problem:** Hero section uses `min-height: 70vh`, which can behave poorly on mobile browser UI chrome transitions.  
   **Why it matters:** Content can jump/crop when URL bars collapse/expand, especially on iOS Safari and Android Chrome.  
   **Suggested fix:** Prefer safer viewport units with fallback, e.g. `min-height: min(760px, 70svh); min-height: min(760px, 70dvh);`.  
   **Estimated effort:** S  
   **Risk:** Low

5. **Problem:** Desktop-to-mobile switch for nav occurs at `940px`, making 768px tablet rely on hamburger by default even in landscape.  
   **Why it matters:** Navigation discoverability is lower on tablet where horizontal space could support inline links.  
   **Suggested fix:** Re-evaluate breakpoint (e.g. 820px/860px) or use container-query-driven nav based on actual header width instead of viewport-only cutoff.  
   **Estimated effort:** M  
   **Risk:** Low

6. **Problem:** Small button/input tap-target heights are borderline on mobile (e.g., compact variants around ~40–43px).  
   **Why it matters:** WCAG touch target guidance and real-world usability favor >=44px targets.  
   **Suggested fix:** Raise minimum interactive size via shared utility (`min-height: 44px`) for nav toggle, `.button-small`, form inputs/checkbox hit areas.  
   **Estimated effort:** S  
   **Risk:** Low

7. **Problem:** Major images are delivered as full-size JPGs without `srcset`/`sizes` variants.  
   **Why it matters:** Mobile users may download oversized assets, slowing render and increasing data usage.  
   **Suggested fix:** Generate responsive image variants and add `srcset`/`sizes`; add explicit width/height attributes where possible to reduce CLS risk.  
   **Estimated effort:** M  
   **Risk:** Medium (asset pipeline touch)

8. **Problem:** Long CTA rows (e.g., catering action cluster) become visually dense on small screens.  
   **Why it matters:** Action overload can reduce conversion and increase accidental taps.  
   **Suggested fix:** Use progressive disclosure on mobile (show top 1–2 actions + “More options”), or stack with stronger spacing using fluid gap tokens.  
   **Estimated effort:** M  
   **Risk:** Low

9. **Problem:** Section spacing is mostly static (`padding: 4rem`) regardless of viewport.  
   **Why it matters:** At 320–390px, static spacing can feel cramped inside cards while still wasting vertical real estate between sections.  
   **Suggested fix:** Introduce fluid spacing scale with `clamp()` for section/card padding and inter-component gaps.  
   **Estimated effort:** S  
   **Risk:** Low

10. **Problem:** Typography is partly fluid (headings), but body text remains fixed; line lengths vary unpredictably in some cards/sections.  
    **Why it matters:** Readability suffers at extremes (small phones and wide desktop).  
    **Suggested fix:** Add constrained measure (`max-width: 65ch`) to long paragraphs and modest fluid body scaling (`clamp(0.98rem, 0.92rem + 0.2vw, 1.06rem)`).  
    **Estimated effort:** S  
    **Risk:** Low

## Quick wins (< 1 hour)

- Add global focus-visible styles for all form controls.
- Increase minimum tap target size to 44px for nav toggle, small buttons, and inputs.
- Replace `70vh` with `svh/dvh` fallback strategy in hero.
- Reduce mobile embed heights with `clamp()` to improve above-the-fold content.
- Add `max-width` text measure utility (`.measure`) and apply to long copy blocks.

## Code-level recommendations (examples)

### 1) Safer viewport units + fluid spacing/type

```css
.hero {
  min-height: min(760px, 70vh);   /* fallback */
  min-height: min(760px, 70svh);  /* mobile-safe */
}

:root {
  --space-2: clamp(0.5rem, 0.4rem + 0.4vw, 0.85rem);
  --space-4: clamp(1rem, 0.8rem + 0.8vw, 1.6rem);
  --space-8: clamp(2rem, 1.4rem + 2vw, 4rem);
  --text-body: clamp(0.98rem, 0.92rem + 0.2vw, 1.06rem);
}

body { font-size: var(--text-body); }
.menu, .reviews, .about-page { padding: var(--space-8) 0; }
```

### 2) Embed containment + mobile sizing

```css
.menu-widget iframe {
  width: 100%;
  min-height: clamp(300px, 55svh, 780px);
}

.facebook-embed iframe {
  width: min(100%, 500px);
  height: clamp(360px, 60svh, 680px);
}
```

### 3) Interaction/accessibility upgrades

```css
a:focus-visible,
button:focus-visible,
input:focus-visible,
select:focus-visible,
textarea:focus-visible {
  outline: 2px solid var(--accent-2);
  outline-offset: 3px;
}

.button,
.button-small,
.menu-toggle,
.signup-grid input {
  min-height: 44px;
}
```

```js
// nav keyboard close + focus return (pattern)
menuToggle.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') closeMenu();
});

document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && nav.classList.contains('open')) {
    closeMenu();
    menuToggle.focus();
  }
});
```

### 4) Container-query path for header nav (optional)

```css
.nav-wrap {
  container-type: inline-size;
}

@container (min-width: 760px) {
  .menu-toggle { display: none; }
  .site-nav {
    position: static;
    width: auto;
    display: flex;
    flex-direction: row;
    background: transparent;
    border: 0;
    padding: 0;
  }
}
```

## Validation plan

### Commands

```bash
python3 scripts/build-site.py
python3 -m http.server 4173 --directory pigsheadbbq/site/pigsheadbbq.com
```

(If lint/typecheck/tests are later added, run: lint → typecheck → test → build in that order.)

### Manual viewport/device checks

- Verify no horizontal scroll at 320, 375, 390, 414, 768, 1024, 1280, 1440.
- Open/close nav via touch and keyboard; ensure Escape closes and focus returns.
- Confirm all interactive controls are >=44px target size.
- Validate hero/menu/facebook embeds on iOS Safari + Android Chrome with URL bar expanded/collapsed.
- Check signup form labels, focus states, and error message wrapping at 200% zoom.

### Regression checklist

- Header remains sticky and non-overlapping with skip-link/focus ring.
- No change to brand color palette/typography identity beyond fluid scaling.
- Menu + Facebook embeds still load and remain functional.
- CTA links (`tel`, `mailto`, PDF download) continue working.
- About page and footer layout remain stable across breakpoints.

## Evidence captured

- Full-page screenshots captured at each requested breakpoint:
  - 320, 375, 390, 414, 768, 1024, 1280, 1440
- Note: This audit is recommendation-only; no UI fixes were applied yet, so no “after” screenshots exist in this pass.
