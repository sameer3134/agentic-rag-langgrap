---
model: claude-sonnet-4-0
complexity: advanced
priority: high
tags: ["state", "frontend", "components"]
depends_on: []
chains_to: []
skip_if: ["no_frontend"]
version: 1.0.0

---

## Graphify Context
{{GRAPH_IMPORTANCE_LOGIC}}
> Instruction to future Claude: "If this module is identified as a 'Core Node' by Graphify, apply 2x stricter linting and testing rules."

# State Management Architecture for {{FE_FRAMEWORK}}

You are an expert {{FE_FRAMEWORK}} architect specializing in state management with {{FE_STATE_MANAGER}}. You write production-grade {{FE_LANGUAGE}} and follow {{NAMING_CONVENTION}} conventions throughout.

## Arguments

$ARGUMENTS — Describe the feature, domain, or state problem you need solved. Include any constraints (offline support, real-time sync, multi-tab, SSR hydration).

---

## 1. State Architecture Analysis

Before writing any code, classify every piece of state in the feature described by $ARGUMENTS into exactly one of these categories:

| Category | Ownership | Lifetime | Examples |
|---|---|---|---|
| **Local UI state** | Single component | Mount/unmount cycle | Form input values, toggle flags, accordion open/close |
| **Shared UI state** | Component subtree | Session | Theme, sidebar collapsed, modal stack |
| **Global client state** | Application-wide | Session or persisted | Auth tokens, user preferences, feature flags |
| **Server state** | Backend / {{DB_TYPE}} | Cache TTL | Entities fetched from {{BE_PATH_API}}, paginated lists |
| **URL state** | Browser | Navigation | Filters, sort order, pagination cursors, active tab |

Output a markdown table mapping each identified piece of state to its category, the recommended storage mechanism in {{FE_STATE_MANAGER}}, and the invalidation strategy.

---

## 2. Store Design Patterns

Design the store structure following {{FE_STATE_MANAGER}} idioms.

### If using Redux Toolkit / Zustand slices:
```{{FE_LANGUAGE}}
// {{FE_PATH_SRC}}/store/slices/<domain>Slice.ts
// Each slice owns one bounded context. Never cross-reference slice internals.
// Export actions and selectors only — never raw state shape.
```

### If using Jotai / Recoil atoms:
```{{FE_LANGUAGE}}
// {{FE_PATH_SRC}}/atoms/<domain>.ts
// Base atoms are private. Derived atoms are the public API.
// Atom families for parameterized state (entity by ID).
```

### If using MobX / Valtio modules:
```{{FE_LANGUAGE}}
// {{FE_PATH_SRC}}/stores/<domain>Store.ts
// One observable class per domain. Computed getters for derived data.
// Actions are the only mutation path — enforce strict mode.
```

**Rules for all approaches:**
- Co-locate the store definition with its selectors, actions, and types in the same directory.
- Place shared types in `{{FE_PATH_SRC}}/types/<domain>.types.ts`.
- Name files using {{NAMING_CONVENTION}}.
- Every store module must have a corresponding test file at `{{FE_PATH_TESTS}}/store/<domain>.test.ts`.

---

## 3. Data Fetching Layer Integration

Integrate server state management with the data fetching layer. Choose the pattern that matches {{FE_STATE_MANAGER}}:

### RTK Query (Redux Toolkit)
```{{FE_LANGUAGE}}
// {{FE_PATH_SRC}}/services/<domain>Api.ts
// - Define endpoints using builder.query / builder.mutation
// - Use providesTags / invalidatesTags for automatic cache invalidation
// - transformResponse to normalize before caching
// - baseQuery points to {{BE_PATH_API}}
```

### TanStack Query (framework-agnostic)
```{{FE_LANGUAGE}}
// {{FE_PATH_HOOKS}}/queries/use<Domain>Query.ts
// - queryKey factory: const <domain>Keys = { all: [...], detail: (id) => [...] }
// - staleTime / gcTime tuned per endpoint volatility
// - placeholderData for instant UI while revalidating
// - Custom hook wraps useQuery and returns domain-typed result
```

### SWR Pattern
```{{FE_LANGUAGE}}
// {{FE_PATH_HOOKS}}/swr/use<Domain>.ts
// - Key generator keeps cache keys consistent
// - Deduplication window configured globally
// - revalidateOnFocus / revalidateOnReconnect per-hook
// - Fallback data from SSR / static props when applicable
```

Ensure every data fetching hook:
1. Handles loading, error, and empty states explicitly.
2. Returns a typed result object, never raw library internals.
3. Logs fetch failures to your observability layer.
4. Respects {{DB_TYPE}} cache semantics (ETag, Cache-Control) where available.

---

## 4. Optimistic Updates and Cache Invalidation

```{{FE_LANGUAGE}}
// Pattern: Optimistic mutation with rollback
//
// 1. Snapshot current cache state
// 2. Apply optimistic update to cache immediately
// 3. Fire mutation to {{BE_PATH_API}}
// 4. On success: reconcile server response with cache (server wins)
// 5. On failure: rollback to snapshot, surface error to UI
//
// For {{FE_STATE_MANAGER}}, implement this as:
// - RTK Query: onQueryStarted + dispatch(api.util.updateQueryData(...))
// - TanStack Query: onMutate + queryClient.setQueryData / cancelQueries
// - SWR: optimisticData option + rollbackOnError
// - Zustand/Jotai: wrap set() in try/catch with previous-value capture
```

Cache invalidation rules:
- **Time-based**: Set stale time per query based on data volatility.
- **Event-based**: Invalidate on mutation success, WebSocket message, or focus.
- **Manual**: Provide a `refresh` action for user-triggered refetch.
- **Cascade**: When a parent entity changes, invalidate all child queries.

---

## 5. State Normalization

Normalize server entities to avoid data duplication and stale references:

```{{FE_LANGUAGE}}
// {{FE_PATH_UTILS}}/normalize.ts

// Flat entity map: Record<EntityId, Entity>
// Separate ID arrays for ordering: EntityId[]
// Lookup is O(1) by ID, list rendering uses the ID array.

// For {{FE_STATE_MANAGER}}, use:
// - RTK: createEntityAdapter (provides selectAll, selectById, etc.)
// - Manual: normalize on fetch, denormalize in selectors
// - normalizr library if entity relationships are deeply nested

// Example shape:
// {
//   entities: { [id: string]: DomainEntity },
//   ids: string[],
//   meta: { totalCount: number, cursor: string | null }
// }
```

**When to normalize**: Any entity referenced in more than one query or displayed in both list and detail views. **When to skip**: Simple config objects, UI-only state, data displayed once and discarded.

---

## 6. Derived and Computed State

Never store values that can be computed. Define selectors / derived atoms / computed properties instead.

```{{FE_LANGUAGE}}
// {{FE_PATH_SRC}}/selectors/<domain>Selectors.ts

// Rules:
// 1. Selectors are pure functions of state — no side effects.
// 2. Compose small selectors into larger ones (bottom-up).
// 3. Memoize with createSelector (Reselect), derived atoms, or computed().
// 4. Parameterized selectors accept arguments via factory pattern.
//
// Example (Redux):
//   export const selectFilteredItems = createSelector(
//     [selectAllItems, selectActiveFilter],
//     (items, filter) => items.filter(matchesFilter(filter))
//   );
//
// Example (Jotai):
//   export const filteredItemsAtom = atom((get) => {
//     const items = get(allItemsAtom);
//     const filter = get(activeFilterAtom);
//     return items.filter(matchesFilter(filter));
//   });
```

Place all selectors adjacent to their store/atom definition. Export them as the public read API. Components must never access raw state shape directly.

---

## 7. State Persistence

Persist selected state slices across sessions. Choose the right storage per data type:

| Storage | Use For | Limits | Security |
|---|---|---|---|
| `localStorage` | User preferences, feature flags, theme | ~5 MB | No secrets |
| `sessionStorage` | Form drafts, wizard progress | ~5 MB | Tab-scoped |
| `URL search params` | Filters, pagination, shareable view state | ~2 KB practical | Public |
| `IndexedDB` | Large datasets, offline cache | Generous | No secrets |
| `Cookie` | Auth tokens (httpOnly, secure) | 4 KB | Server-readable |

```{{FE_LANGUAGE}}
// {{FE_PATH_UTILS}}/persistence.ts
//
// Implement a persistence middleware/plugin for {{FE_STATE_MANAGER}}:
// 1. Serialize only allow-listed keys (never persist tokens or PII in localStorage).
// 2. Version the persisted schema — migrate on load if version mismatch.
// 3. Debounce writes (300ms) to avoid thrashing storage on rapid state changes.
// 4. Handle quota exceeded gracefully — warn, do not crash.
// 5. For URL state, use {{FE_FRAMEWORK}} router integration to keep URL and store in sync.
```

---

## 8. DevTools Setup and Debugging

Configure developer tooling for observability into state:

```{{FE_LANGUAGE}}
// {{FE_PATH_SRC}}/store/devtools.ts

// Redux: Redux DevTools Extension — enabled in dev, stripped in production.
//   - Configure action sanitizer to redact sensitive payloads.
//   - Set maxAge to prevent memory leaks in long sessions.
//
// Zustand: devtools() middleware wrapping the store.
//
// Jotai: jotai-devtools provider — displays atom dependency graph.
//
// TanStack Query: ReactQueryDevtools component — shows cache entries and timing.
//
// MobX: mobx-devtools or spy() for action logging.

// Production guards:
// if (process.env.NODE_ENV === 'development') { enableDevTools(); }

// Custom logging middleware:
// Log action type + duration. Warn if reducer takes > 16ms (frame budget).
```

Add a `{{FE_PATH_SRC}}/store/debugUtils.ts` exporting helper functions:
- `dumpState()` — serializes current store to console or clipboard.
- `rehydrateState(json)` — loads a serialized snapshot for reproduction.
- `traceSelectors(selectorName)` — logs every recomputation with inputs/output.

---

## 9. Migration Strategies

When migrating between state management solutions (e.g., Redux to Zustand, Context to Jotai):

1. **Inventory phase**: Catalog all stores, selectors, and subscribers. Map dependencies.
2. **Adapter layer**: Create a facade that exposes the same hook API (`use<Domain>()`) backed by the new implementation. Components do not change.
3. **Incremental migration**: Migrate one domain/slice at a time behind the facade. Run both old and new in parallel during transition.
4. **Validation**: For each migrated slice, verify:
   - All tests in `{{FE_PATH_TESTS}}/store/` pass with `{{FE_TEST_COMMAND}}`.
   - Lint passes with `{{FE_LINT_COMMAND}}`.
   - Build succeeds with `{{FE_BUILD_COMMAND}}`.
   - No regressions in selector output (snapshot tests help).
5. **Cleanup**: Remove old implementation, adapters, and legacy dependencies.

```{{FE_LANGUAGE}}
// {{FE_PATH_HOOKS}}/use<Domain>.ts  <-- Stable public API (facade)
//
// Phase 1: export const useDomain = () => useOldStore(oldSelector);
// Phase 2: export const useDomain = () => useNewStore(newSelector);
//
// Components import useDomain and are unaffected by the swap.
```

---

## 10. Testing State Logic

Test state in isolation from components using {{FE_TEST_FRAMEWORK}}.

```{{FE_LANGUAGE}}
// {{FE_PATH_TESTS}}/store/<domain>.test.ts

// A. Unit tests for reducers / store actions:
//    - Given initial state + action, assert next state.
//    - Cover edge cases: empty collections, duplicate IDs, missing fields.
//    - Test action creators produce correct payloads.

// B. Selector tests:
//    - Given a known state shape, assert selector output.
//    - Verify memoization: call twice with same input, expect === reference equality.
//    - Test parameterized selectors with multiple arguments.

// C. Async / data fetching tests:
//    - Mock {{BE_PATH_API}} responses (MSW or manual mocks).
//    - Assert loading -> success state transitions.
//    - Assert loading -> error state transitions.
//    - Verify cache key structure and invalidation triggers.

// D. Optimistic update tests:
//    - Simulate mutation success: assert final cache matches server response.
//    - Simulate mutation failure: assert rollback to pre-mutation snapshot.

// E. Integration tests (state + component):
//    - Render component with test store provider.
//    - Interact via user events, assert UI reflects state changes.
//    - Use {{FE_TEST_FRAMEWORK}} utilities for async assertions (waitFor, findBy).
```

Run with:
```bash
{{FE_TEST_COMMAND}} --coverage -- {{FE_PATH_TESTS}}/store/
```

---

## 11. Performance Optimization

### Selector Memoization
- Use `createSelector` (Reselect) or equivalent to avoid recomputation.
- Never create selectors inside render — define them at module scope or via `useMemo`.
- For parameterized selectors, use factory functions that return memoized selectors.

### Subscription Optimization
```{{FE_LANGUAGE}}
// {{FE_PATH_SRC}}/store/subscriptions.ts

// Redux: useSelector with shallow equality check for object/array returns.
//   import { shallowEqual } from 'react-redux';
//   const data = useSelector(selectDerivedData, shallowEqual);

// Zustand: Use slice selectors to subscribe to minimal state.
//   const count = useStore((s) => s.items.length);  // re-renders only when length changes

// Jotai: Atoms are already granular. Split large atoms into focused ones.
//   Avoid derived atoms that depend on too many base atoms.

// MobX: observer() HOC auto-tracks access. Keep render methods lean.
```

### Render Prevention Checklist
1. **Avoid new references in selectors** — returning `array.filter()` in every call creates a new array. Memoize it.
2. **Avoid inline object creation** in `useSelector` — `useSelector(s => ({ a: s.a, b: s.b }))` creates a new object every time. Use `shallowEqual` or split into two `useSelector` calls.
3. **Batch dispatches** — multiple synchronous dispatches cause multiple re-renders. Use `batch()` (React-Redux) or action grouping.
4. **Lazy initialization** — for expensive initial state, pass a factory function: `useState(() => computeExpensiveDefault())`.
5. **Windowing** — for large lists driven by state, use `react-window` or `@tanstack/react-virtual` to render only visible items.

### Performance Profiling
```bash
# Profile re-renders caused by state changes
# React DevTools Profiler -> Record -> Interact -> Review "Why did this render?"

# Measure selector recomputations
# Reselect: selectorFn.recomputations()
# Custom: wrap selector in traceSelectors() from debugUtils.ts

# Validate bundle does not include devtools in production
{{FE_BUILD_COMMAND}} && npx source-map-explorer dist/assets/*.js
```

---

## Output Requirements

When generating code for $ARGUMENTS, produce the following files:

1. **Store definition** — `{{FE_PATH_SRC}}/store/<domain>` with types, actions, selectors, and reducer/store.
2. **Data fetching hooks** — `{{FE_PATH_HOOKS}}/queries/use<Domain>*.ts` with typed query/mutation hooks.
3. **Persistence config** — `{{FE_PATH_UTILS}}/persistence/<domain>Persistence.ts` if state requires persistence.
4. **Test suite** — `{{FE_PATH_TESTS}}/store/<domain>.test.ts` covering all categories from section 10.
5. **Index barrel** — `{{FE_PATH_SRC}}/store/<domain>/index.ts` re-exporting the public API only.

All code must:
- Be written in {{FE_LANGUAGE}} with strict type safety (no `any`).
- Follow {{NAMING_CONVENTION}} conventions.
- Pass `{{FE_LINT_COMMAND}}` with zero warnings.
- Pass `{{FE_TEST_COMMAND}}` with full coverage on store logic.
- Include JSDoc comments on every exported function and type.

---

> Self-Hydrating System Note: When this template is hydrated, replace all `{{PLACEHOLDER}}` tokens with values from the project configuration. If a value is unknown, prompt the user before generating code. Never assume defaults for framework or tooling choices.
