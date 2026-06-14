---
model: claude-sonnet-4-0
complexity: advanced
priority: medium
tags: ["design-system", "frontend", "components", "scaffold"]
depends_on: []
chains_to: []
skip_if: ["no_frontend"]
version: 1.0.0

---

## Graphify Context
{{GRAPH_IMPORTANCE_LOGIC}}
> Instruction to future Claude: "If this module is identified as a 'Core Node' by Graphify, apply 2x stricter linting and testing rules."

# Design System Architecture

You are building a production-grade, self-hydrating design system for a {{FE_FRAMEWORK}} application written in {{FE_LANGUAGE}}, styled with {{FE_STYLE_SYSTEM}}, and bundled with {{FE_BUNDLER}}. Every component must be accessible (WCAG AA minimum), themeable, and independently publishable.

$ARGUMENTS

---

## 1. Token System

All visual decisions are encoded as tokens. No raw values may appear in component code.

### 1.1 Color Tokens

Define a semantic color scale in `{{FE_PATH_STYLES}}/tokens/colors.ts`:

```
// Primitive palette (never referenced directly by components)
--color-blue-50 through --color-blue-900
--color-neutral-0 through --color-neutral-1000

// Semantic tokens (components use these exclusively)
--color-bg-primary, --color-bg-secondary, --color-bg-inverse
--color-fg-default, --color-fg-muted, --color-fg-accent, --color-fg-on-emphasis
--color-border-default, --color-border-muted, --color-border-emphasis
--color-status-success, --color-status-warning, --color-status-error, --color-status-info
```

### 1.2 Spacing Tokens

Use a 4px base unit scale in `{{FE_PATH_STYLES}}/tokens/spacing.ts`:

```
--space-0: 0        --space-1: 4px      --space-2: 8px
--space-3: 12px     --space-4: 16px     --space-5: 20px
--space-6: 24px     --space-8: 32px     --space-10: 40px
--space-12: 48px    --space-16: 64px    --space-20: 80px
```

### 1.3 Typography Tokens

Define in `{{FE_PATH_STYLES}}/tokens/typography.ts`:

```
--font-family-sans, --font-family-mono, --font-family-serif
--font-size-xs: 12px   --font-size-sm: 14px   --font-size-base: 16px
--font-size-lg: 18px   --font-size-xl: 20px   --font-size-2xl: 24px
--font-size-3xl: 30px  --font-size-4xl: 36px
--font-weight-regular: 400  --font-weight-medium: 500  --font-weight-bold: 700
--line-height-tight: 1.25   --line-height-normal: 1.5  --line-height-relaxed: 1.75
--letter-spacing-tight: -0.02em  --letter-spacing-normal: 0  --letter-spacing-wide: 0.04em
```

### 1.4 Shadow, Border, and Motion Tokens

```
// Shadows
--shadow-sm, --shadow-md, --shadow-lg, --shadow-xl, --shadow-inner, --shadow-none

// Border radii
--radius-none: 0  --radius-sm: 4px  --radius-md: 8px  --radius-lg: 12px  --radius-full: 9999px

// Motion
--duration-instant: 0ms   --duration-fast: 100ms   --duration-normal: 200ms  --duration-slow: 400ms
--easing-default: cubic-bezier(0.4, 0, 0.2, 1)
--easing-in: cubic-bezier(0.4, 0, 1, 1)
--easing-out: cubic-bezier(0, 0, 0.2, 1)
```

All tokens must be exported both as CSS custom properties and as {{FE_LANGUAGE}} constants for use in {{FE_STYLE_SYSTEM}}.

---

## 2. Component Library Structure (Atomic Design)

Organize components under `{{FE_PATH_COMPONENTS}}/` using atomic design principles and the `{{FILE_NAMING_CONVENTION}}` naming convention:

```
{{FE_PATH_COMPONENTS}}/
  atoms/
    Button/
      Button.{{FE_LANGUAGE}}x       # Component implementation
      Button.styles.ts               # Style definitions
      Button.test.ts                 # Unit + interaction tests
      Button.stories.ts              # Storybook stories
      Button.a11y.test.ts            # Dedicated accessibility tests
      index.ts                       # Barrel export
    Text/
    Icon/
    Input/
    Badge/
    Avatar/
    Spinner/
    Divider/
  molecules/
    InputGroup/
    Card/
    FormField/
    MenuItem/
    SearchBar/
    Pagination/
    Breadcrumb/
  organisms/
    Header/
    Sidebar/
    DataTable/
    Form/
    Modal/
    CommandPalette/
    NavigationMenu/
  layouts/
    Stack/
    Grid/
    Container/
    Spacer/
    AspectRatio/
```

Every component directory must contain all five files listed above. Use `{{NAMING_CONVENTION}}` for all exported identifiers.

---

## 3. Variant System

Implement a composable variant system. Each component defines its variants explicitly:

```typescript
// Example: Button variants
type ButtonProps = {
  size: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  variant: 'solid' | 'outline' | 'ghost' | 'link';
  colorScheme: 'primary' | 'secondary' | 'danger' | 'success' | 'neutral';
  state: 'default' | 'hover' | 'active' | 'focus' | 'disabled' | 'loading';
  fullWidth?: boolean;
};
```

Rules:
- Every variant combination must be visually tested via Storybook.
- Variant props must have sensible defaults so bare `<Button>` renders correctly.
- Compound variants (e.g., `solid` + `danger` + `disabled`) must be explicitly styled — never rely on cascading overrides.

---

## 4. Theme Architecture

### 4.1 CSS Custom Properties

Theme values are expressed as CSS custom properties on `:root` and overridden via `[data-theme="dark"]`:

```css
:root {
  --color-bg-primary: var(--color-neutral-0);
  --color-fg-default: var(--color-neutral-900);
}
[data-theme="dark"] {
  --color-bg-primary: var(--color-neutral-900);
  --color-fg-default: var(--color-neutral-50);
}
```

### 4.2 Brand Theming

Support arbitrary brand overrides via a theme config object in `{{FE_PATH_STYLES}}/themes/`:

```
themes/
  default.ts       # Base light theme
  dark.ts          # Dark mode overrides
  brand-a.ts       # Client / white-label brand overrides
  brand-b.ts
  index.ts         # createTheme() utility
```

The `createTheme()` utility must deep-merge a brand config onto the base theme and inject the resulting CSS custom properties at runtime.

### 4.3 System Preference Detection

Respect `prefers-color-scheme` by default, allow user override stored in `localStorage`, and expose a `useTheme()` hook that returns `{ theme, setTheme, resolvedTheme }`.

---

## 5. Icon System

Place icon assets under `{{FE_PATH_ASSETS}}/icons/`:

- Maintain a single SVG sprite file for build-time inlining.
- Expose each icon as a tree-shakeable named export from `{{FE_PATH_COMPONENTS}}/atoms/Icon/icons/index.ts`.
- The `<Icon>` component accepts `name`, `size`, `color`, and `aria-label` props.
- All decorative icons must set `aria-hidden="true"`. Informational icons must require an `aria-label`.
- Run `{{FE_BUILD_COMMAND}}` to verify the icon bundle stays under 20 KB gzipped.

---

## 6. Layout Primitives

Implement the following layout components in `{{FE_PATH_COMPONENTS}}/layouts/`:

| Component   | Purpose                                              |
|-------------|------------------------------------------------------|
| `Stack`     | Vertical or horizontal flex layout with gap control  |
| `Grid`      | CSS Grid wrapper with responsive column definitions  |
| `Container` | Max-width centered wrapper with responsive padding   |
| `Spacer`    | Invisible spacing element consuming flex space       |
| `AspectRatio` | Maintains a fixed width-to-height ratio            |

Each layout primitive must:
- Accept a polymorphic `as` prop to render as any HTML element.
- Support responsive prop values via breakpoint objects: `{ base: 4, md: 8, lg: 12 }`.
- Forward refs and spread remaining props onto the root element.

---

## 7. Form Components

Build form controls in `{{FE_PATH_COMPONENTS}}/atoms/` and compose them in `{{FE_PATH_COMPONENTS}}/molecules/FormField/`:

| Component   | Features                                                       |
|-------------|----------------------------------------------------------------|
| `Input`     | Text, password, email, number, search. Prefix/suffix slots.   |
| `Select`    | Native and custom dropdown. Searchable. Multi-select option.   |
| `Checkbox`  | Indeterminate state. Group wrapper.                            |
| `Radio`     | RadioGroup context. Horizontal/vertical layout.                |
| `Switch`    | Toggle with on/off labels. Loading state.                      |
| `Textarea`  | Auto-resize option. Character count.                           |

Validation rules:
- Every form control must support `error`, `helperText`, and `required` props.
- Integrate with {{FE_FRAMEWORK}} form libraries (e.g., React Hook Form, Formik, VeeValidate) via controlled and uncontrolled modes.
- Associate labels and error messages with inputs via `aria-labelledby` and `aria-describedby`.
- Run `{{FE_LINT_COMMAND}}` to enforce consistent form markup patterns.

---

## 8. Feedback Components

Implement the following in `{{FE_PATH_COMPONENTS}}/organisms/` (or molecules where appropriate):

### Toast / Notification
- Managed via a `ToastProvider` context and `useToast()` hook.
- Supports `success`, `error`, `warning`, `info` variants.
- Auto-dismiss with configurable duration. Pause on hover.
- Respects `prefers-reduced-motion`.
- Announces via `aria-live="polite"` (or `assertive` for errors).

### Alert
- Inline, dismissible alert banners with icon, title, description, and action slots.

### Modal / Dialog
- Focus trap, scroll lock, Escape to close.
- `aria-modal="true"`, returns focus to trigger on close.
- Nested modals must stack correctly.

### Drawer
- Slide-in panel from any edge. Shares Modal's focus management.

### Tooltip
- Trigger on hover/focus. Delay configurable. `role="tooltip"` with `aria-describedby`.

### Popover
- Trigger on click. Contains interactive content. Uses floating-ui / Popper for positioning.

---

## 9. Documentation

### 9.1 Storybook Setup

Configure Storybook in `{{FE_PATH_SRC}}/.storybook/`:

```
.storybook/
  main.ts           # Addons: a11y, controls, docs, viewport, themes
  preview.ts        # Global decorators, theme provider
  manager.ts        # UI customization
```

Every component story file must include:
- A `Default` story showing the component with default props.
- A `Playground` story with full `args` controls.
- An `AllVariants` story rendering every size/color/state combination in a grid.
- A `Docs` page with usage guidelines, do/don't examples, and prop table auto-generated from TypeScript types.

### 9.2 Props Documentation

Use TSDoc comments on every public prop. Example:

```typescript
interface ButtonProps {
  /** The visual style of the button */
  variant?: 'solid' | 'outline' | 'ghost' | 'link';
  /** Renders a spinner and disables interaction */
  isLoading?: boolean;
}
```

Run `{{FE_BUILD_COMMAND}}` to generate the static docs site.

---

## 10. Versioning and Changelog

- Follow [Conventional Commits](https://www.conventionalcommits.org/) for every change to the design system.
- Use Changesets or standard-version to automate `CHANGELOG.md` generation.
- Semver rules:
  - **Patch**: bug fixes, token value tweaks that do not affect layout.
  - **Minor**: new components, new variants, non-breaking token additions.
  - **Major**: removed components, renamed tokens, breaking prop API changes.
- Tag each release as `@{{NAMING_CONVENTION}}/design-system@x.y.z` in git.
- Publish a migration guide for every major bump in `{{FE_PATH_SRC}}/docs/migrations/`.

---

## 11. Accessibility

Every component must satisfy the following before merge:

1. **Keyboard navigation**: all interactive elements reachable and operable via keyboard alone.
2. **Screen reader**: correct roles, labels, and live regions. Test with VoiceOver + Safari and NVDA + {{FE_BROWSER}}.
3. **Color contrast**: WCAG AA (4.5:1 for normal text, 3:1 for large text) verified via `{{FE_A11Y_TOOL}}`.
4. **Focus indicators**: visible focus ring using `--color-border-emphasis`. Never `outline: none` without a replacement.
5. **Motion**: honor `prefers-reduced-motion`. Disable transitions and animations when set.
6. **Zoom**: UI must remain usable at 200% browser zoom.
7. **Aria patterns**: follow [WAI-ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apd/) for every widget pattern (combobox, dialog, tabs, etc.).

Run `{{FE_A11Y_TOOL}}` checks as part of `{{FE_TEST_COMMAND}}`. Block CI on any new violations.

---

## 12. Testing Strategy

### 12.1 Visual Regression

- Use Chromatic or Percy connected to Storybook.
- Capture snapshots for every story in light and dark themes.
- Require approval for any visual diff before merge.
- Run in `{{CLOUD_CI_TOOL}}` pipeline at `{{CLOUD_PATH_CI}}`.

### 12.2 Interaction Tests

- Use `{{FE_TEST_FRAMEWORK}}` with `{{FE_RUNNER}}` for unit and interaction tests.
- Test keyboard flows, click handlers, form submission, focus management.
- Minimum 90% branch coverage per component.

### 12.3 Accessibility Tests

- Run `{{FE_A11Y_TOOL}}` (e.g., axe-core) programmatically in every component test file (`*.a11y.test.ts`).
- Storybook a11y addon must show zero violations on every story.

### 12.4 Commands

```bash
# Run all design system tests
{{FE_TEST_COMMAND}}

# Run linting
{{FE_LINT_COMMAND}}

# Build the design system package
{{FE_BUILD_COMMAND}}
```

---

## 13. Package Publishing Strategy

### 13.1 Monorepo Structure

```
packages/
  design-tokens/         # Tokens only — zero runtime dependencies
    package.json
  design-system/         # Components, hooks, utilities
    package.json
  design-system-icons/   # Icon library — tree-shakeable
    package.json
  design-system-docs/    # Storybook static site
    package.json
```

### 13.2 Build and Publish

- Build with `{{FE_BUNDLER}}` targeting ESM and CJS outputs.
- Generate TypeScript declaration files.
- Publish to npm (or internal registry) via `{{CLOUD_CI_TOOL}}` on tagged releases.
- Each package lists explicit peer dependencies (`{{FE_FRAMEWORK}}`, `{{FE_STYLE_SYSTEM}}`).
- Tree-shaking: verify via bundlesize CI check that unused components are not included in consumer bundles.

### 13.3 CI Pipeline

Define in `{{CLOUD_PATH_CI}}`:

```yaml
steps:
  - name: Install
    run: npm ci
  - name: Lint
    run: {{FE_LINT_COMMAND}}
  - name: Test
    run: {{FE_TEST_COMMAND}}
  - name: Accessibility
    run: {{FE_A11Y_TOOL}} --ci
  - name: Build
    run: {{FE_BUILD_COMMAND}}
  - name: Visual Regression
    run: npx chromatic --exit-zero-on-changes
  - name: Publish (on tag)
    if: startsWith(github.ref, 'refs/tags/')
    run: npm publish --workspaces
```

---

## Self-Hydration Checklist

Before considering this design system ready for production:

- [ ] All tokens exported as CSS custom properties and {{FE_LANGUAGE}} constants
- [ ] Every component has unit tests, a11y tests, stories, and style files
- [ ] Light and dark themes render correctly across all components
- [ ] Storybook builds and deploys without warnings
- [ ] `{{FE_TEST_COMMAND}}` passes with 90%+ coverage
- [ ] `{{FE_LINT_COMMAND}}` reports zero errors
- [ ] `{{FE_A11Y_TOOL}}` reports zero WCAG AA violations
- [ ] Visual regression baselines captured and approved
- [ ] Package builds produce valid ESM, CJS, and type declarations
- [ ] CHANGELOG.md updated via Conventional Commits
- [ ] Migration guide written for any breaking changes
- [ ] CI pipeline at `{{CLOUD_PATH_CI}}` runs all checks on every PR
