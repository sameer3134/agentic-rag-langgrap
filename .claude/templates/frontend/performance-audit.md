---
model: claude-sonnet-4-0
complexity: advanced
priority: high
tags: ["performance", "frontend", "monitoring"]
depends_on: []
chains_to: []
skip_if: ["no_frontend"]
version: 1.0.0

---

## Graphify Context
{{GRAPH_IMPORTANCE_LOGIC}}
> Instruction to future Claude: "If this module is identified as a 'Core Node' by Graphify, apply 2x stricter linting and testing rules."

# Frontend Performance Audit -- Self-Hydrating System

You are a senior frontend performance engineer. Conduct a thorough performance audit of the
{{FE_FRAMEWORK}} application written in {{FE_LANGUAGE}}, bundled with {{FE_BUNDLER}}, and
styled using {{FE_STYLE_SYSTEM}}. The application runs on {{FE_RUNTIME}}.

Audit target: $ARGUMENTS (defaults to the full application if not specified).

---

## 1. Core Web Vitals Analysis

Measure and evaluate all Core Web Vitals for the target pages. For each metric, identify the
root cause of any regression and propose a concrete fix with expected impact.

### 1.1 Largest Contentful Paint (LCP)
- Identify the LCP element on each key route. Inspect `{{FE_PATH_SRC}}` for render-blocking
  resources (synchronous scripts, render-blocking CSS, large hero images).
- Check server response time (TTFB) and resource load waterfall.
- Verify that the LCP resource uses `rel="preload"` or `fetchpriority="high"` where applicable.
- Target: LCP < 2.5 s on 75th percentile.

### 1.2 First Input Delay (FID) / Interaction to Next Paint (INP)
- Profile main-thread JavaScript during page load and interaction using {{FE_A11Y_TOOL}}.
- Look for long tasks (> 50 ms) in `{{FE_PATH_SRC}}` that block user input.
- Evaluate event handler complexity in `{{FE_PATH_COMPONENTS}}`.
- Target: INP < 200 ms on 75th percentile.

### 1.3 Cumulative Layout Shift (CLS)
- Audit images, ads, embeds, and dynamically injected content for missing dimensions.
- Inspect CSS in `{{FE_STYLE_SYSTEM}}` files for layout-triggering animations.
- Verify font loading strategy (font-display, preload) to prevent FOIT/FOUT shifts.
- Target: CLS < 0.1 on 75th percentile.

---

## 2. Bundle Analysis -- Code Splitting, Tree Shaking, Lazy Loading

Analyze the {{FE_BUNDLER}} output to minimize shipped JavaScript.

### 2.1 Bundle Size Inventory
```bash
{{FE_BUILD_COMMAND}}
```
- Generate and review the bundle stats (e.g., `webpack-bundle-analyzer`, `vite-bundle-visualizer`,
  or equivalent for {{FE_BUNDLER}}).
- List every chunk > 50 kB (gzipped) and classify as critical-path vs. deferrable.

### 2.2 Code Splitting
- Verify route-level splitting: each route in `{{FE_PATH_SRC}}` should produce its own chunk.
- Identify shared vendor chunks that could be split further.
- Check dynamic `import()` usage for heavy libraries (charting, rich-text editors, etc.).

### 2.3 Tree Shaking
- Confirm `sideEffects: false` is set correctly in package.json for internal packages.
- Look for barrel-file re-exports in `{{FE_PATH_COMPONENTS}}` that defeat tree shaking.
- Validate that dead code from feature flags is eliminated at build time.

### 2.4 Lazy Loading
- Audit below-the-fold components for `React.lazy` / dynamic imports / equivalent in {{FE_FRAMEWORK}}.
- Ensure Suspense boundaries (or framework equivalent) provide meaningful loading states.

---

## 3. Render Performance

### 3.1 Unnecessary Re-renders
- Instrument `{{FE_PATH_COMPONENTS}}` with React DevTools Profiler (or framework equivalent).
- Identify components that re-render without prop/state changes.
- Check for inline object/array/function creation in JSX that breaks shallow comparison.

### 3.2 Memoization
- Audit usage of `useMemo`, `useCallback`, `React.memo` (or framework equivalents).
- Flag over-memoization (trivial computations) and under-memoization (expensive computations
  or large lists passed as props).

### 3.3 Virtualization
- For lists or tables with > 50 rows, verify windowed/virtualized rendering is in place.
- Measure scroll performance (jank) with and without virtualization.

---

## 4. Image and Asset Optimization

### 4.1 Image Formats
- Audit `{{FE_PATH_ASSETS}}` for images not in next-gen formats (WebP, AVIF).
- Verify the build pipeline converts or serves modern formats with fallbacks.

### 4.2 Lazy Loading and Responsive Images
- Ensure all below-the-fold images use `loading="lazy"` and `decoding="async"`.
- Check for `srcset` and `sizes` attributes to serve resolution-appropriate images.
- Verify the hero/LCP image is NOT lazy-loaded.

### 4.3 CDN and Caching
- Confirm static assets in `{{FE_PATH_ASSETS}}` are served via CDN with immutable
  cache headers and content-hashed filenames.
- Verify Cache-Control headers: `public, max-age=31536000, immutable` for hashed assets.

---

## 5. Network Optimization

### 5.1 Resource Hints
- Audit `<link rel="preconnect">` for critical third-party origins.
- Add `<link rel="prefetch">` for likely next-navigation resources.
- Use `<link rel="preload">` for critical fonts, LCP images, and above-the-fold CSS.

### 5.2 Service Worker and Offline Caching
- Review service worker registration and caching strategy (cache-first, stale-while-revalidate).
- Verify precached assets match the {{FE_BUNDLER}} output manifest.
- Ensure cache invalidation works correctly on deployment.

### 5.3 HTTP/2+ and Compression
- Confirm the server supports HTTP/2 or HTTP/3 with multiplexed streams.
- Verify Brotli (preferred) or Gzip compression for all text-based assets.
- Check for unnecessary request waterfalls that could be parallelized.

---

## 6. JavaScript Execution Profiling

### 6.1 Long Tasks
- Use Chrome DevTools Performance panel or {{FE_A11Y_TOOL}} to identify tasks > 50 ms.
- Trace each long task back to its source in `{{FE_PATH_SRC}}`.
- Propose yielding strategies (`requestIdleCallback`, `scheduler.yield()`, chunked processing).

### 6.2 Main Thread Blocking
- Measure Total Blocking Time (TBT) and correlate with INP.
- Identify synchronous layout/style recalculations (forced reflows).
- Move heavy computation to Web Workers where feasible.

### 6.3 Script Evaluation Cost
- Profile parse + compile + execute time for each bundle chunk.
- Flag polyfills or legacy transforms shipped to modern browsers unnecessarily.

---

## 7. CSS Performance

### 7.1 Critical CSS Extraction
- Verify that above-the-fold CSS is inlined in the initial HTML response.
- Defer non-critical CSS using `media="print"` swap or async loading patterns.
- Check {{FE_STYLE_SYSTEM}} configuration for critical CSS extraction support.

### 7.2 Unused CSS Removal
- Run PurgeCSS or equivalent against `{{FE_PATH_SRC}}` to measure unused CSS percentage.
- Target: < 10% unused CSS in production bundles.
- Remove or tree-shake unused utility classes from {{FE_STYLE_SYSTEM}}.

### 7.3 CSS Containment and Layers
- Apply `contain: layout style paint` to isolated widget components.
- Evaluate `@layer` usage to reduce specificity conflicts and selector complexity.

---

## 8. Memory Leak Detection

### 8.1 Detached DOM Nodes
- Take heap snapshots before and after navigating between routes.
- Search for detached DOM trees that persist after component unmount.
- Verify cleanup in `useEffect` return functions (or framework lifecycle equivalent).

### 8.2 Event Listener Cleanup
- Audit `addEventListener` calls in `{{FE_PATH_COMPONENTS}}` for matching `removeEventListener`.
- Check for global event listeners (window resize, scroll) that outlive their component.
- Verify `AbortController` usage for fetch calls to prevent stale closures.

### 8.3 Closure and Timer Leaks
- Identify `setInterval`/`setTimeout` calls without corresponding cleanup on unmount.
- Look for closures capturing large objects (DOM references, large arrays) that prevent GC.
- Profile memory growth during repeated user interactions (open/close modal, paginate).

---

## 9. Third-Party Script Impact Analysis

- Inventory all third-party scripts (analytics, ads, chat widgets, tag managers).
- Measure each script's impact on TBT, LCP, and bundle size using {{FE_A11Y_TOOL}}.
- Classify scripts: critical (auth, payments) vs. deferrable (analytics, chat).
- Recommend `async`/`defer` attributes, facade patterns, or Partytown for non-critical scripts.
- Verify that third-party scripts are loaded from `<link rel="preconnect">` origins.
- Check for CORS and SameSite cookie issues causing redundant requests.

---

## 10. Server-Side Rendering / Static Generation Performance

Evaluate the {{FE_FRAMEWORK}} SSR/SSG pipeline for optimal self-hydration.

### 10.1 Hydration Performance
- Measure time-to-interactive after SSR HTML is painted.
- Identify components that trigger full-page re-render during hydration (hydration mismatch).
- Evaluate partial/selective/progressive hydration strategies available in {{FE_FRAMEWORK}}.

### 10.2 Static Generation
- Identify pages that can be statically generated at build time vs. requiring SSR.
- Verify ISR (Incremental Static Regeneration) or equivalent is configured for semi-dynamic pages.
- Measure build time for static generation:
```bash
{{FE_BUILD_COMMAND}}
```

### 10.3 Streaming SSR
- Check if {{FE_FRAMEWORK}} supports streaming SSR and whether it is enabled.
- Verify Suspense boundaries are placed to allow progressive HTML streaming.
- Measure TTFB improvement from streaming vs. buffered SSR.

---

## 11. Lighthouse / WebPageTest Automation

### 11.1 Automated Audits
- Run {{FE_A11Y_TOOL}} in CI mode against critical user flows:
```bash
{{FE_START_COMMAND}}
# Then in a separate process:
# npx lighthouse http://localhost:3000 --output=json --output-path=./lighthouse-report.json
```
- Parse results for Core Web Vitals, accessibility, best practices, and SEO scores.

### 11.2 WebPageTest Integration
- Configure WebPageTest scripts for key user journeys (landing, search, checkout).
- Compare filmstrip results across deployments to catch visual regressions.
- Monitor Speed Index and Visually Complete metrics over time.

### 11.3 Real User Monitoring (RUM)
- Verify `web-vitals` library (or equivalent) is reporting LCP, INP, CLS to analytics.
- Compare lab data (Lighthouse) with field data (CrUX, RUM) for discrepancies.
- Set up alerting for p75 metric regressions in production.

---

## 12. Performance Budgets and CI Integration

### 12.1 Define Performance Budgets
- JavaScript budget: < 300 kB gzipped total, < 150 kB per route chunk.
- CSS budget: < 50 kB gzipped total.
- Image budget: < 200 kB per above-the-fold image.
- LCP budget: < 2.5 s, INP budget: < 200 ms, CLS budget: < 0.1.

### 12.2 CI Enforcement with {{CLOUD_CI_TOOL}}
- Add bundle size check to `{{CLOUD_PATH_CI}}`:
```yaml
# Example CI step for {{CLOUD_CI_TOOL}}
- name: Check bundle size
  run: |
    {{FE_BUILD_COMMAND}}
    npx bundlesize --config bundlesize.config.json
- name: Run Lighthouse CI
  run: |
    npm install -g @lhci/cli
    lhci autorun --config=lighthouserc.json
```
- Fail the build if any budget is exceeded.
- Post Lighthouse score diff as a PR comment for visibility.

### 12.3 Trend Tracking
- Store historical performance data (Lighthouse scores, bundle sizes) per commit.
- Generate dashboards showing performance trends over the last 30 deployments.
- Alert the team when any metric degrades by > 10% from the rolling baseline.

---

## 13. Mobile Performance Considerations

### 13.1 Device and Network Simulation
- Test on simulated mid-tier devices (Moto G Power, 4x CPU throttle, Slow 3G).
- Verify touch targets meet minimum 48x48 px requirement.
- Measure performance with `Save-Data` header respected.

### 13.2 Responsive Performance
- Ensure `{{FE_PATH_COMPONENTS}}` does not load desktop-only assets on mobile viewports.
- Verify that viewport-based code splitting delivers smaller bundles to mobile.
- Check for layout thrashing caused by responsive breakpoint recalculations.

### 13.3 PWA Readiness
- Validate the Web App Manifest and service worker for installability.
- Test offline experience with network disabled.
- Measure start-up performance from home screen launch (standalone mode).

---

## Test Verification

Run the test suite to confirm nothing is broken after applying optimizations:
```bash
{{FE_TEST_COMMAND}}
```

---

## Deliverables

Produce the following artifacts at the end of this audit:

1. **Performance Scorecard** -- table of all Core Web Vitals with current values, targets, and status.
2. **Prioritized Issue List** -- each issue ranked by user-impact (High/Medium/Low) with estimated effort.
3. **Bundle Analysis Report** -- chunk inventory with sizes, owners, and split recommendations.
4. **Optimization Roadmap** -- phased plan (Quick Wins < 1 day, Short-Term < 1 sprint, Long-Term).
5. **CI Configuration** -- updated `{{CLOUD_PATH_CI}}` with performance budget enforcement.
6. **Monitoring Setup** -- RUM integration code and alerting thresholds.

Focus on measurable improvements. Every recommendation must include an expected metric delta
(e.g., "Lazy-loading the charting library will reduce initial JS by ~80 kB, improving LCP by
~300 ms on median connections"). Prioritize changes by impact-to-effort ratio.
