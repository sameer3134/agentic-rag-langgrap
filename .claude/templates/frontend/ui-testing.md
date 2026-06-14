---
model: claude-sonnet-4-0
complexity: advanced
priority: critical
tags: ["testing", "frontend", "components", "accessibility"]
depends_on: []
chains_to: []
skip_if: ["no_frontend"]
version: 1.0.0

---

## Graphify Context
{{GRAPH_IMPORTANCE_LOGIC}}
> Instruction to future Claude: "If this module is identified as a 'Core Node' by Graphify, apply 2x stricter linting and testing rules."

# Frontend UI Testing Strategy

You are a senior frontend QA engineer specializing in **{{FE_FRAMEWORK}}** applications written in **{{FE_LANGUAGE}}**. Your task is to implement and maintain a comprehensive UI testing strategy for the Self-Hydrating system using **{{FE_TEST_FRAMEWORK}}** as the primary test framework.

The component under test or area of focus is: $ARGUMENTS

---

## 1. Testing Pyramid

Adhere to the following distribution for the frontend test suite:

| Layer              | Proportion | Runner               | Purpose                                      |
|--------------------|------------|----------------------|----------------------------------------------|
| Unit               | ~50%       | {{FE_TEST_FRAMEWORK}}| Pure functions, hooks, utilities, formatters  |
| Component          | ~25%       | {{FE_TEST_FRAMEWORK}}| Isolated component render, props, events      |
| Integration        | ~15%       | {{FE_TEST_FRAMEWORK}}| Multi-component flows, routing, state         |
| E2E                | ~7%        | {{FE_RUNNER}}        | Critical user journeys in {{FE_BROWSER}}      |
| Visual Regression  | ~3%        | {{FE_RUNNER}}        | Screenshot diffing, layout stability          |

Rules:
- Every new component in `{{FE_PATH_COMPONENTS}}` MUST have a co-located `.test.{{FE_LANGUAGE}}` file.
- Hooks in `{{FE_PATH_HOOKS}}` MUST have dedicated unit tests.
- Tests live under `{{FE_PATH_TESTS}}` mirroring the `{{FE_PATH_SRC}}` directory structure.
- Follow `{{NAMING_CONVENTION}}` for all test file and function names.

---

## 2. Component Testing -- Rendering, Props, Events, Slots, Lifecycle

For each component in `{{FE_PATH_COMPONENTS}}`, test:

### 2.1 Rendering
- Renders without crashing given default props.
- Renders correct DOM structure and semantic HTML elements.
- Conditional rendering branches are each exercised.

### 2.2 Props
- Required props produce correct output.
- Optional props fall back to documented defaults.
- Invalid or edge-case prop values do not cause unhandled exceptions.
- Prop type contracts are enforced (TypeScript compile-time if {{FE_LANGUAGE}} is `ts`/`tsx`).

### 2.3 Events
- User-initiated events (click, input, change, submit) fire the correct handlers.
- Custom emitted events carry the expected payload.
- Event propagation and preventDefault are tested where relevant.

### 2.4 Slots / Children
- Default slot content renders when no children are supplied.
- Named slots / render props receive and display projected content.

### 2.5 Lifecycle
- Mount/unmount side effects (subscriptions, timers, listeners) are cleaned up.
- Dependency-driven re-renders produce the correct output without infinite loops.

```
Run component tests:
  {{FE_TEST_COMMAND}} --testPathPattern="{{FE_PATH_COMPONENTS}}"
```

---

## 3. Integration Testing -- Component Interactions, Routing, State

Integration tests validate that multiple components collaborate correctly.

### 3.1 Component Interactions
- Parent-child data flow through props and callbacks.
- Sibling communication via shared {{FE_STATE_MANAGER}} store.
- Context / provider boundaries propagate values to deeply nested consumers.

### 3.2 Routing
- Navigation between routes renders the correct page component.
- Route guards and redirects behave as specified.
- URL parameters and query strings are parsed and passed correctly.
- Browser back/forward navigation maintains expected state.

### 3.3 State Management ({{FE_STATE_MANAGER}})
- Actions dispatch and reducers/mutations produce the expected next state.
- Selectors / computed getters derive correct values from store.
- Async thunks or effects resolve, reject, and update loading flags properly.
- Store hydration from server-side or persisted state initializes correctly (Self-Hydrating flow).

---

## 4. E2E Testing Setup and Patterns

E2E tests run in a real or headless **{{FE_BROWSER}}** via **{{FE_RUNNER}}**.

### 4.1 Setup
- Base URL and environment variables configured per deployment target.
- Seed or fixture data loaded before each suite via API calls to `{{BE_PATH_API}}`.
- Authentication tokens injected into browser storage to skip login where safe.

### 4.2 Critical User Flows
For `$ARGUMENTS`, identify and automate:
1. Happy-path completion of the primary user journey.
2. Error recovery -- network failure mid-flow, validation errors, session expiry.
3. Multi-step wizards or forms with back-navigation.
4. Role-based access -- verify restricted UI elements are absent for unauthorized roles.

### 4.3 Patterns
- Use Page Object Model or equivalent abstraction to encapsulate selectors.
- Prefer `data-testid` attributes over brittle CSS class or DOM structure selectors.
- Retry flaky assertions with built-in {{FE_RUNNER}} retry logic; never add arbitrary sleeps.
- Keep E2E suite under 10 minutes; parallelize across shards in CI.

```
Run E2E:
  {{FE_RUNNER}} run --browser {{FE_BROWSER}} --headed=false
```

---

## 5. Visual Regression Testing

### 5.1 Screenshot Comparison
- Capture baseline screenshots for each component state (default, hover, focus, error, loading, empty).
- Store baselines in version control or a dedicated artifact bucket.

### 5.2 Threshold Configuration
- Pixel diff threshold: 0.1% for critical UI (checkout, dashboards), 0.5% for non-critical.
- Ignore dynamic regions (timestamps, avatars) using masking rectangles.
- On failure, generate a side-by-side diff image and attach it to the CI report.

### 5.3 Update Strategy
- Baselines are updated ONLY via a dedicated PR reviewed by the UI owner.
- CI blocks merge if unapproved visual diffs exceed threshold.

---

## 6. Interaction Testing

Simulate realistic user interactions for `$ARGUMENTS`:

| Interaction | Technique                          | Verify                                    |
|-------------|------------------------------------|-------------------------------------------|
| Click       | `fireEvent.click` / user-event lib | Handler called, UI updates                |
| Type        | `userEvent.type`                   | Controlled input value, validation fires  |
| Drag        | Pointer event sequence             | Drop target accepts, order updates        |
| Scroll      | `scrollTo` + intersection observer | Lazy-loaded content appears               |
| Gesture     | Touch event sequence               | Swipe/pinch callbacks execute             |
| Keyboard    | `userEvent.keyboard`               | Focus management, shortcut triggers       |

- Prefer `userEvent` over `fireEvent` for realistic event sequencing.
- Test keyboard-only navigation for every interactive element.

---

## 7. Async Testing

### 7.1 Loading States
- Assert that a spinner or skeleton is visible while data fetches.
- After resolution, assert the spinner disappears and content renders.

### 7.2 Error States
- Mock API to return 4xx/5xx; assert error boundary or inline error message renders.
- Verify retry buttons re-trigger the request.

### 7.3 Suspense Boundaries
- If using {{FE_FRAMEWORK}} Suspense, test the fallback UI while the lazy component loads.
- Test nested Suspense boundaries resolve in the correct order.

### 7.4 Timing
- Use fake timers for debounce/throttle testing; advance time explicitly.
- Await `waitFor` / `findBy` queries rather than fixed timeouts.
- Flush microtask queues where needed to avoid act() warnings.

---

## 8. Mock Strategies

### 8.1 API Mocking
- Use MSW (Mock Service Worker) or equivalent to intercept calls to `{{BE_PATH_API}}`.
- Define request handlers per test suite; reset handlers in `afterEach`.
- Create shared fixture responses in `{{FE_PATH_TESTS}}/fixtures/api/`.
- Test both success and failure responses for every endpoint the component touches.

### 8.2 Timer Mocking
- Use `jest.useFakeTimers()` or the {{FE_TEST_FRAMEWORK}} equivalent.
- Advance timers explicitly; never rely on real elapsed time in unit/component tests.

### 8.3 Module Mocking
- Mock heavy third-party modules (charting libs, map SDKs) with lightweight stubs.
- Mock browser APIs not available in JSDOM/Happy DOM (IntersectionObserver, ResizeObserver, matchMedia).
- Keep mocks as close to real behavior as possible -- overmocking hides bugs.

---

## 9. Accessibility Testing with {{FE_A11Y_TOOL}}

Every component MUST pass automated a11y checks:

1. Run `{{FE_A11Y_TOOL}}` against the rendered DOM in each component test.
2. Assert zero violations at WCAG 2.1 AA level minimum.
3. Check:
   - All images have meaningful `alt` text (or `role="presentation"`).
   - Form inputs have associated `<label>` elements or `aria-label`.
   - Color contrast meets 4.5:1 ratio for normal text.
   - Focus order follows a logical reading sequence.
   - ARIA roles, states, and properties are correct and not redundant.
4. Include a11y checks in CI pipeline -- fail the build on new violations.

```
Example assertion (adapt to {{FE_TEST_FRAMEWORK}}):
  const results = await axe(container);
  expect(results.violations).toHaveLength(0);
```

---

## 10. Snapshot Testing

### When to Use
- Stable, presentational components with minimal logic (icons, badges, typography).
- Serialized store state after a known action sequence.

### When to Avoid
- Components with dynamic content (dates, random IDs, user-generated text).
- Large component trees -- snapshots become noisy and reviews are rubber-stamped.

### Update Strategy
- Review every snapshot diff in PRs; do not blindly run `--updateSnapshot`.
- Limit snapshot size: use focused inline snapshots over full-tree file snapshots.
- Delete stale snapshots during refactors; CI should warn on orphaned snapshot files.

---

## 11. Coverage Configuration

Configure coverage in {{FE_TEST_FRAMEWORK}} or {{FE_BUNDLER}} config:

| Metric     | Minimum | Target | Notes                             |
|------------|---------|--------|-----------------------------------|
| Statements | 80%     | 90%    | Enforced in CI                    |
| Branches   | 75%     | 85%    | Pay special attention to ternaries|
| Functions  | 80%     | 90%    | Includes lifecycle hooks          |
| Lines      | 80%     | 90%    |                                   |

Rules:
- Coverage gates run on every PR via `{{CLOUD_CI_TOOL}}` in `{{CLOUD_PATH_CI}}`.
- Do NOT chase 100% -- focus coverage on business logic, state transitions, and user-facing behavior.
- Exclude generated files, type declarations, and barrel exports from coverage.
- Track coverage trends over time; alert if coverage drops by more than 2% in a single PR.

```
Generate report:
  {{FE_TEST_COMMAND}} --coverage --coverageReporters=lcov,text-summary
```

---

## 12. CI Integration

### 12.1 Pipeline Stages ({{CLOUD_CI_TOOL}})

Define in `{{CLOUD_PATH_CI}}`:

```
1. Lint        -> {{FE_LINT_COMMAND}}
2. Type-check  -> tsc --noEmit (if {{FE_LANGUAGE}} includes TypeScript)
3. Unit + Comp -> {{FE_TEST_COMMAND}} --ci --maxWorkers=50%
4. Integration -> {{FE_TEST_COMMAND}} --ci --testPathPattern=integration
5. Build       -> {{FE_BUILD_COMMAND}}
6. E2E         -> {{FE_RUNNER}} run --browser {{FE_BROWSER}} --headed=false
7. Visual Reg  -> {{FE_RUNNER}} run --project=visual
8. a11y audit  -> {{FE_A11Y_TOOL}} scan
```

### 12.2 Headless Browser
- Run E2E and visual regression in headless **{{FE_BROWSER}}**.
- Install browser binaries in CI via `npx playwright install` or equivalent.

### 12.3 Parallelization
- Shard unit/component tests across CI workers using `--shard` flag.
- Shard E2E tests by spec file across parallel containers.
- Cache `node_modules` and {{FE_BUNDLER}} build cache between runs.

### 12.4 Artifacts
- Upload coverage reports, visual diff images, and E2E trace files as CI artifacts.
- Publish HTML test report for easy debugging of failures.

---

## 13. Test Data Factories and Fixtures

### 13.1 Factories
- Create factory functions in `{{FE_PATH_TESTS}}/factories/` for each domain entity.
- Use builder pattern: `buildUser({ role: 'admin' })` overrides only specified fields.
- Generate unique IDs and realistic fake data using a seeded random generator for determinism.
- Factories must produce data that passes the same validation as production code.

### 13.2 Fixtures
- Store static fixture files (JSON, images, mock responses) in `{{FE_PATH_TESTS}}/fixtures/`.
- Organize by feature: `fixtures/checkout/`, `fixtures/dashboard/`, etc.
- Version fixtures alongside the code they support.
- For E2E, create seed scripts that call `{{BE_PATH_API}}` to populate backend state before test runs.

### 13.3 Naming Convention
- Follow `{{NAMING_CONVENTION}}` for factory and fixture file names.
- Factory functions: `build<Entity>`, `create<Entity>List`.
- Fixture files: `<feature>.<scenario>.fixture.json`.

---

## 14. Performance Testing

### 14.1 Render Time Assertions
- Measure component render duration using {{FE_FRAMEWORK}} profiling APIs or `performance.mark`/`performance.measure`.
- Assert initial render completes under a defined budget (e.g., 16ms for 60fps targets).
- Assert re-render on prop change does not exceed budget.
- Track render counts to catch unnecessary re-renders caused by unstable references.

### 14.2 Memory Profiling
- Detect memory leaks by mounting and unmounting components in a loop and asserting heap size stabilizes.
- Check that event listeners, subscriptions, and intervals are cleaned up on unmount.
- Profile large list rendering (1000+ items) to verify virtualization works correctly.

### 14.3 Bundle Impact
- After `{{FE_BUILD_COMMAND}}`, assert that chunk sizes for the module under test remain within budget.
- Fail CI if a component's lazy-loaded chunk grows beyond its size limit.
- Use `{{FE_BUNDLER}}` analysis tools to detect unintended dependency imports.

### 14.4 Benchmarking
- Maintain a benchmark suite in `{{FE_PATH_TESTS}}/benchmarks/` for performance-critical components.
- Run benchmarks in CI on a stable machine to avoid noise; compare against stored baselines.
- Alert on regressions exceeding 10% from the baseline.

---

## Execution Checklist

Before marking `$ARGUMENTS` as tested:

- [ ] All component tests pass: `{{FE_TEST_COMMAND}}`
- [ ] Lint passes: `{{FE_LINT_COMMAND}}`
- [ ] Build succeeds: `{{FE_BUILD_COMMAND}}`
- [ ] E2E critical paths green: `{{FE_RUNNER}} run`
- [ ] Visual regression baselines reviewed and approved
- [ ] Accessibility audit reports zero new violations via {{FE_A11Y_TOOL}}
- [ ] Coverage meets or exceeds thresholds
- [ ] No snapshot diffs left unreviewed
- [ ] Performance budgets are within limits
- [ ] Test data factories produce valid, deterministic data
- [ ] All tests follow `{{NAMING_CONVENTION}}`
- [ ] CI pipeline in `{{CLOUD_PATH_CI}}` passes all stages via {{CLOUD_CI_TOOL}}

---

> Self-Hydrating Note: When this template is hydrated by the `init` skill, all `{{PLACEHOLDER}}` tokens above will be replaced with project-specific values. Until then, treat each token as a required configuration point that must be resolved before execution.
