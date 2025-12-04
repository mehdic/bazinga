---
name: react
type: framework
priority: 2
token_estimate: 600
compatible_with: [developer, senior_software_engineer]
requires: [typescript, javascript]
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# React Engineering Expertise

## Specialist Profile
React specialist building performant, accessible UIs. Expert in hooks, Server Components, and modern React patterns.

---

## Patterns to Follow

### Component Architecture
<!-- version: react >= 18 -->
- **Server Components by default**: Only use `'use client'` when needed (Next.js App Router)
<!-- version: react < 18 -->
- **Client-side rendering**: No Server Components; use data fetching libraries
<!-- version: react >= 16.8 -->
- **Functional components**: No class components for new code
- **Single responsibility**: One purpose per component
- **Composition over props**: Use children and render props
- **Colocation**: Keep related code together

### React 19 Patterns
<!-- version: react >= 19 -->
- **useActionState for forms**: Replaces useFormState with clearer semantics
- **useOptimistic for UI**: Optimistic updates built-in
- **use() for promises**: Cleaner async data handling
- **React Compiler**: Auto-memoization reduces useMemo/useCallback need

### Hooks Best Practices
<!-- version: react >= 16.8 -->
- **Custom hooks for reuse**: Extract logic into `use*` functions
- **Dependency arrays**: Include all reactive values
- **Cleanup functions**: Return cleanup from useEffect
- **useReducer for complex state**: When state has multiple sub-values
<!-- version: react >= 19 -->
- **useMemo/useCallback rarely**: React Compiler auto-memoizes; use for ref stability only
<!-- version: react >= 16.8, react < 19 -->
- **useMemo/useCallback sparingly**: Only for measured performance issues

### State Management
- **Lift state minimally**: Only as high as needed
- **Context for global state**: Theme, auth, locale
- **Server state libraries**: TanStack Query, SWR for async
- **URL state**: searchParams for shareable state

### Performance
- **Code splitting**: Dynamic imports for large components
- **Suspense boundaries**: Wrap async components
- **Error boundaries**: Catch rendering errors gracefully
- **Key props**: Stable, unique keys for lists

---

## Patterns to Avoid

### Component Anti-Patterns
- ❌ **`'use client'` everywhere**: Ship unnecessary JS; default to server
- ❌ **Props drilling >3 levels**: Use context or composition
- ❌ **Inline object/array literals in JSX**: Creates new reference each render
- ❌ **Missing key props**: Causes reconciliation bugs
- ❌ **Index as key**: Breaks state on reorder; use stable IDs

### Hook Anti-Patterns
- ❌ **useEffect for derived state**: Use useMemo or compute in render
- ❌ **useEffect for data fetching** (React 19+): Use Server Components or use()
- ❌ **Missing dependencies**: Stale closures cause bugs
- ❌ **State for props transformation**: Just compute it
- ❌ **useEffect as "Swiss Army knife"**: Use proper patterns instead

### State Anti-Patterns
- ❌ **Storing derived values**: Compute from source of truth
- ❌ **Redundant state**: One source per piece of data
- ❌ **State updates in render**: Causes infinite loops
- ❌ **Global state for local needs**: Keep state close to usage

### Performance Anti-Patterns
- ❌ **Premature optimization**: Measure before memoizing
- ❌ **Over-memoizing**: React Compiler handles most cases
- ❌ **Large component trees**: Split and lazy load
- ❌ **Direct DOM manipulation**: Use refs and React patterns

---

## Verification Checklist

### Architecture
- [ ] Server Components for non-interactive UI
- [ ] Client Components only for hooks/events
- [ ] Proper component composition
- [ ] Code splitting for large bundles

### Hooks
- [ ] Custom hooks for reusable logic
- [ ] Complete dependency arrays
- [ ] Cleanup functions where needed
- [ ] No useEffect abuse

### Performance
- [ ] Suspense boundaries for async
- [ ] Error boundaries for fault tolerance
- [ ] Stable key props on lists
- [ ] Bundle size monitored

### Accessibility
- [ ] Semantic HTML elements
- [ ] ARIA attributes for custom widgets
- [ ] Keyboard navigation
- [ ] Focus management

---

## Code Patterns (Reference)

### Recommended Constructs
<!-- version: react >= 16.8 -->
- **Functional component**: `function UserCard({ user }: Props) { return <div>{user.name}</div>; }`
- **Custom hook**: `function useUser(id: string) { /* fetch logic */ return { user, loading }; }`
<!-- version: react >= 16 -->
- **Error boundary**: Wrap fallible subtrees with error UI fallback
<!-- version: react >= 18 -->
- **Suspense for data**: `<Suspense fallback={<Spinner />}><AsyncComponent /></Suspense>`
- **useTransition**: `const [isPending, startTransition] = useTransition()` for non-urgent updates
- **useDeferredValue**: `const deferred = useDeferredValue(value)` for expensive computations
<!-- version: react >= 16.6, react < 18 -->
- **Suspense for lazy**: `<Suspense fallback={<Spinner />}><LazyComponent /></Suspense>` (code-splitting only)
<!-- version: react >= 19 -->
- **useActionState**: `const [state, action, pending] = useActionState(serverAction, initial)`
- **useOptimistic**: `const [optimistic, setOptimistic] = useOptimistic(state)`
- **use()**: `const data = use(promise)` inside component

