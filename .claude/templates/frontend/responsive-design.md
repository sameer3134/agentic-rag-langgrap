---
model: claude-sonnet-4-0
complexity: intermediate
priority: high
tags: ["responsive", "frontend", "components", "accessibility"]
depends_on: []
chains_to: []
skip_if: ["no_frontend"]
version: 1.0.0

---

## Graphify Context
{{GRAPH_IMPORTANCE_LOGIC}}
> Instruction to future Claude: "If this module is identified as a 'Core Node' by Graphify, apply 2x stricter linting and testing rules."

# Responsive Design Audit & Implementation

You are a senior frontend engineer specializing in responsive design, mobile-first architecture, and cross-device UX. Perform a thorough audit and implementation pass on the project described below.

$ARGUMENTS

## Project Context

- **Framework**: {{FE_FRAMEWORK}}
- **Language**: {{FE_LANGUAGE}}
- **Style System**: {{FE_STYLE_SYSTEM}}
- **Bundler**: {{FE_BUNDLER}}
- **Test Framework**: {{FE_TEST_FRAMEWORK}}
- **Test Command**: {{FE_TEST_COMMAND}}
- **Target Browser(s)**: {{FE_BROWSER}}
- **Accessibility Tooling**: {{FE_A11Y_TOOL}}
- **Naming Convention**: {{NAMING_CONVENTION}}

### Key Paths

| Purpose | Path |
|---|---|
| Components | {{FE_PATH_COMPONENTS}} |
| Stylesheets | {{FE_PATH_STYLES}} |
| Source Root | {{FE_PATH_SRC}} |
| Static Assets | {{FE_PATH_ASSETS}} |

---

## 1. Breakpoint Strategy

Audit the current breakpoint definitions. Determine whether the project follows a **mobile-first** or **desktop-first** approach and verify consistency.

### Requirements

- Enumerate every breakpoint token defined in {{FE_PATH_STYLES}} (e.g., `sm`, `md`, `lg`, `xl`, `2xl`).
- Confirm that media queries use `min-width` (mobile-first) or `max-width` (desktop-first) consistently. Flag any mixed usage.
- Ensure breakpoints align with the design system in {{FE_STYLE_SYSTEM}}. If custom breakpoints exist, verify they are documented.
- Check for hardcoded pixel values in component files under {{FE_PATH_COMPONENTS}} that bypass the token system.

### Deliverables

- A canonical breakpoint map (token -> pixel value -> typical device class).
- A list of violations where raw pixel values appear instead of breakpoint tokens.
- A recommendation on whether to adopt container queries for component-scoped responsiveness.

---

## 2. Layout Systems

Audit usage of CSS Grid, Flexbox, and container queries across {{FE_PATH_COMPONENTS}}.

### Requirements

- Identify the primary layout strategy per page or route layout component.
- Verify that Grid is used for two-dimensional layouts and Flexbox for one-dimensional flows. Flag misuse.
- Check for container query support where components need to respond to their parent container rather than the viewport.
- Ensure layout components in {{FE_FRAMEWORK}} use semantic HTML landmarks (`<main>`, `<nav>`, `<aside>`, `<section>`) rather than generic `<div>` nesting.
- Validate that no layout causes horizontal overflow at any defined breakpoint.

### Deliverables

- Layout inventory table: component name, layout method, responsive behavior.
- Refactoring recommendations for components that would benefit from container queries.

---

## 3. Responsive Typography

Audit the type scale for fluid responsiveness across viewports.

### Requirements

- Verify that a fluid type scale is defined (e.g., using `clamp()`, `calc()`, or viewport units like `vw`/`vi`).
- Check that base font size is not set in `px` on the root element (prefer `rem` or `%` for zoom accessibility).
- Ensure heading hierarchy (`h1`-`h6`) scales proportionally and does not break layout at narrow viewports.
- Validate line-height and measure (line length) stay within readable bounds (45-75 characters) at every breakpoint.
- Review {{FE_STYLE_SYSTEM}} for type scale tokens and confirm component usage matches.

### Deliverables

- Type scale table: token, min size, preferred size, max size.
- List of components with hardcoded font sizes that should use tokens.

---

## 4. Image Responsiveness

Audit image delivery for performance and art direction across devices.

### Requirements

- Verify all content images use `srcset` and `sizes` attributes for resolution switching.
- Check for `<picture>` element usage where art direction is needed (cropping, focal point changes).
- Ensure decorative images use CSS backgrounds or `aria-hidden="true"` and empty `alt` attributes.
- Validate that images in {{FE_PATH_ASSETS}} are served in modern formats (WebP, AVIF) with fallbacks.
- Confirm `loading="lazy"` is applied to below-the-fold images and `fetchpriority="high"` on hero/LCP images.
- Check that `aspect-ratio` or explicit `width`/`height` attributes prevent layout shift (CLS).

### Deliverables

- Image audit report: file, format, has srcset, has sizes, lazy-loaded, CLS-safe.
- Recommendations for missing art direction or format optimization.

---

## 5. Component-Level Responsiveness

Audit how individual components in {{FE_PATH_COMPONENTS}} adapt across breakpoints.

### Requirements

- Check whether components accept responsive props (e.g., `size={{ sm: 'small', lg: 'large' }}`).
- Verify that components use internal breakpoint-aware rendering rather than relying solely on global CSS.
- Ensure render variants (e.g., card list vs. card grid) are handled through props or container queries, not duplicated components.
- Validate that {{FE_FRAMEWORK}} component APIs follow {{NAMING_CONVENTION}} for responsive prop naming.
- Confirm no component uses `display: none` to hide large DOM trees at certain breakpoints when conditional rendering would be more performant.

### Deliverables

- Component responsiveness matrix: component name, responsive props, breakpoint behavior, render variants.
- Refactoring candidates for conditional rendering vs. CSS hiding.

---

## 6. Navigation Patterns

Audit navigation for adaptive behavior across mobile, tablet, and desktop.

### Requirements

- Verify that the primary navigation collapses to a hamburger menu or drawer at mobile breakpoints.
- Check that the mobile menu is keyboard-navigable and traps focus correctly when open.
- Ensure touch targets in mobile navigation meet the 44x44px minimum (WCAG 2.5.8 / Material guidelines).
- Validate that adaptive navigation (e.g., bottom tab bar on mobile, sidebar on desktop) transitions smoothly.
- Confirm that navigation state (open/closed) is managed properly in {{FE_FRAMEWORK}} and does not cause layout jumps.
- Test that the navigation `<nav>` landmark has an accessible label (e.g., `aria-label="Main navigation"`).

### Deliverables

- Navigation behavior table: viewport range, pattern (hamburger/drawer/tab bar/full), interaction model.
- List of navigation accessibility issues.

---

## 7. Touch Target Sizing & Mobile Interaction

Audit interactive elements for mobile usability.

### Requirements

- Verify all tappable elements (buttons, links, form controls) have a minimum touch target of 44x44 CSS pixels.
- Check spacing between adjacent touch targets to prevent mis-taps (minimum 8px gap recommended).
- Ensure hover-dependent interactions (tooltips, dropdown previews) have touch-friendly alternatives.
- Validate that swipe gestures, pull-to-refresh, or other mobile-specific interactions do not conflict with browser gestures.
- Confirm that `pointer` and `hover` media queries are used where appropriate to differentiate touch vs. pointer input.

### Deliverables

- Touch target audit: element, current size, compliant (yes/no), recommended fix.
- List of hover-only interactions that need touch alternatives.

---

## 8. Responsive Forms

Audit form components for mobile usability and input optimization.

### Requirements

- Verify that form inputs use appropriate `inputmode` attributes (`numeric`, `email`, `tel`, `url`, `search`).
- Check that `autocomplete` attributes are set correctly for common fields (name, email, address, payment).
- Ensure form layouts reflow from multi-column to single-column at mobile breakpoints without loss of grouping clarity.
- Validate that on-screen keyboard appearance does not obscure the active input (scroll-into-view behavior).
- Confirm that select elements, date pickers, and custom dropdowns are usable on touch devices.
- Test that form validation messages are visible and associated with their inputs via `aria-describedby`.

### Deliverables

- Form audit table: form name, input count, inputmode usage, autocomplete usage, mobile layout.
- List of forms that need mobile-specific layout or input adjustments.

---

## 9. Dark Mode & Theme Switching

Audit theme support using {{FE_STYLE_SYSTEM}}.

### Requirements

- Verify that `prefers-color-scheme` media query is respected for system-level theme preference.
- Check that a manual theme toggle exists and persists user preference (localStorage or cookie).
- Ensure all color values reference design tokens from {{FE_STYLE_SYSTEM}} rather than hardcoded hex/rgb values.
- Validate that theme transitions are smooth (no flash of unstyled content / FOUC on page load).
- Confirm that contrast ratios meet WCAG AA (4.5:1 for normal text, 3:1 for large text) in both light and dark themes.
- Test that images, icons, and media adapt appropriately to dark mode (e.g., inverted logos, adjusted shadows).

### Deliverables

- Theme token coverage report: tokens with both light/dark values vs. tokens missing a variant.
- Contrast ratio audit for both themes using {{FE_A11Y_TOOL}}.

---

## 10. Visual Regression Testing Across Viewports

Establish or audit viewport-based visual regression tests using {{FE_TEST_FRAMEWORK}}.

### Requirements

- Verify that visual regression snapshots exist for all critical pages at each defined breakpoint.
- Check that the test suite in {{FE_TEST_FRAMEWORK}} captures screenshots at the following minimum viewports:
  - **Mobile**: 375x667 (iPhone SE)
  - **Tablet**: 768x1024 (iPad)
  - **Desktop**: 1440x900 (standard laptop)
  - **Wide**: 1920x1080 (full HD)
- Ensure tests run via `{{FE_TEST_COMMAND}}` and are integrated into the CI pipeline.
- Validate that snapshot diff thresholds are set appropriately (recommend 0.1% pixel diff tolerance).
- Confirm that tests cover both light and dark themes at each viewport.

### Deliverables

- Test coverage matrix: page/component, viewports tested, themes tested, snapshot exists.
- CI integration verification (test command runs in pipeline, failures block merge).

---

## 11. Print Stylesheet Considerations

Audit print styles for pages that users are likely to print.

### Requirements

- Identify printable pages (invoices, reports, articles, receipts) and verify `@media print` styles exist.
- Ensure navigation, footers, sidebars, and interactive elements are hidden in print context.
- Verify that backgrounds, colors, and images are optimized for print (use `color-adjust: exact` where needed).
- Check that page breaks are controlled (`break-before`, `break-after`, `break-inside`) to avoid orphaned headings or split tables.
- Confirm that links display their URLs in print (e.g., via `a[href]::after { content: " (" attr(href) ")"; }`).
- Validate that font sizes and line heights are appropriate for print (typically 12pt body, 1.5 line-height).

### Deliverables

- Print audit: page, has print styles, elements hidden, page breaks controlled, links shown.
- Recommendations for pages that need print stylesheets but lack them.

---

## 12. Accessibility in Responsive Contexts

Audit accessibility under responsive conditions: zoom, reflow, and orientation changes.

### Requirements

- **Zoom (WCAG 1.4.4)**: Verify content is usable at 200% zoom with no horizontal scrolling at 1280px viewport width.
- **Reflow (WCAG 1.4.10)**: Confirm content reflows to a single column at 320px CSS width without loss of information or functionality.
- **Orientation (WCAG 1.3.4)**: Ensure the application does not lock to a single orientation unless essential (e.g., a piano app).
- **Text spacing (WCAG 1.4.12)**: Verify no content is clipped or overlapping when users override letter-spacing, word-spacing, line-height, or paragraph spacing.
- **Target size (WCAG 2.5.8)**: Confirm all interactive targets meet the 24x24px minimum (AA) with 44x44px recommended.
- Run automated checks with {{FE_A11Y_TOOL}} at each breakpoint and review results.
- Test with screen readers at mobile breakpoints to verify reading order matches visual order.

### Deliverables

- Accessibility reflow checklist: page, 200% zoom pass, 320px reflow pass, orientation unlocked.
- List of WCAG violations found per breakpoint.
- Screen reader reading order issues at mobile viewports.

---

## Summary Report Format

After completing all sections, produce a final summary in this structure:

```
### Responsive Design Audit Summary

**Project**: {{FE_FRAMEWORK}} / {{FE_LANGUAGE}} / {{FE_STYLE_SYSTEM}}
**Date**: [audit date]
**Auditor**: Claude (Responsive Design Specialist)

#### Scores (0-10)
| Area | Score | Critical Issues |
|---|---|---|
| Breakpoints | | |
| Layout | | |
| Typography | | |
| Images | | |
| Components | | |
| Navigation | | |
| Touch Targets | | |
| Forms | | |
| Dark Mode | | |
| Visual Regression | | |
| Print Styles | | |
| Accessibility | | |

#### Top 5 Priority Fixes
1. ...
2. ...
3. ...
4. ...
5. ...

#### Estimated Effort
- Quick wins (< 1 day): ...
- Medium effort (1-3 days): ...
- Significant refactors (1+ week): ...
```

---

## Self-Hydrating Instructions

This template is designed for the Self-Hydrating system. When invoked:

1. Resolve all `{{PLACEHOLDER}}` tokens from the project's Graphify context or `.claude/settings.json`.
2. Replace `$ARGUMENTS` with the user-supplied scope or focus area (e.g., "audit the checkout flow" or "implement mobile navigation").
3. Execute each numbered section sequentially. For each section:
   - Read relevant files from the specified paths.
   - Analyze against the stated requirements.
   - Produce the deliverables listed.
4. Compile the final summary report.
5. If any section reveals a "Core Node" (per Graphify), escalate its findings with 2x stricter criteria applied.
