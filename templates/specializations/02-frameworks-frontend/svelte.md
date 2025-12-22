---
name: svelte
type: framework
priority: 2
token_estimate: 550
compatible_with: [developer, senior_software_engineer]
requires: [typescript, javascript]
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Svelte Engineering Expertise

## Specialist Profile
Svelte specialist building reactive, compiled applications. Expert in Svelte 5 runes and SvelteKit.

---

## Patterns to Follow

### Runes (Svelte 5+)
<!-- version: svelte >= 5 -->
- **$state for reactive state**: `let count = $state(0)`
- **$derived for computed**: `let doubled = $derived(count * 2)`
- **$effect for side effects**: Run when dependencies change
- **$props for component props**: `let { user, onselect } = $props()`
- **$bindable for two-way binding**: Opt-in binding support

### State Management
- **Direct mutation allowed**: `items.push(item)` works in Svelte 5
- **Stores for shared state**: writable, readable, derived
- **Context for component trees**: setContext/getContext
- **URL state with SvelteKit**: searchParams for persistence

### Component Patterns
- **Props with defaults**: `let { size = 'md' } = $props()`
- **Snippets over slots**: More powerful, flexible (Svelte 5)
- **Event handlers as props**: Callback props over dispatchers
- **Composition with children**: `{@render children()}`

### SvelteKit
- **load functions for data**: Server and universal loaders
- **Form actions for mutations**: Progressive enhancement
- **Layouts for shared UI**: Nested layouts
- **Error boundaries**: +error.svelte pages

### TypeScript
- **lang="ts" in script**: Full TypeScript support
- **Type props explicitly**: `let { user }: { user: User } = $props()`
- **satisfies for inference**: Maintain type narrowing
- **Generics**: `<script lang="ts" generics="T">`

---

## Patterns to Avoid

### Rune Anti-Patterns
- ❌ **$state changes in $derived**: Causes infinite loops
- ❌ **Multiple event listeners**: Combine into single handler
- ❌ **$: reactive statements (Svelte 5)**: Use $derived/$effect
- ❌ **export let (Svelte 5)**: Use $props() instead

### State Anti-Patterns
- ❌ **Complex state in stores**: Keep stores simple
- ❌ **Mutating store directly**: Use update() or set()
- ❌ **Global state for local needs**: Prefer local $state
- ❌ **Stores without unsubscribe**: Use $ prefix in components

### Component Anti-Patterns
- ❌ **Complex logic in templates**: Extract to script
- ❌ **createEventDispatcher (Svelte 5)**: Use callback props
- ❌ **Slots (Svelte 5)**: Use snippets instead
- ❌ **Heavy computation without $derived**: Cache computed values

### SvelteKit Anti-Patterns
- ❌ **Client-side fetching when load works**: Use loaders
- ❌ **API routes for internal mutations**: Use form actions
- ❌ **Missing error handling**: +error.svelte pages
- ❌ **Skipping prerendering**: SSG when possible

---

## Verification Checklist

### Svelte 5 Runes
- [ ] $state for reactive values
- [ ] $derived for computed values
- [ ] $effect for side effects (sparingly)
- [ ] $props for component inputs

### Component Design
- [ ] TypeScript for props
- [ ] Snippets for slot-like patterns
- [ ] Callback props for events
- [ ] Proper error boundaries

### SvelteKit
- [ ] load functions for data
- [ ] Form actions for mutations
- [ ] Proper layouts and error pages
- [ ] Prerendering where possible

### State Management
- [ ] Local $state preferred
- [ ] Stores for truly shared state
- [ ] Context for component trees
- [ ] URL state for shareable state

---

## Code Patterns (Reference)

### Recommended Constructs
<!-- version: svelte >= 5 -->
- **State**: `let count = $state(0); let doubled = $derived(count * 2);`
- **Props**: `let { user, onselect }: Props = $props();`
- **Effect**: `$effect(() => { console.log(count); });`
- **Snippet**: `{#snippet item(data)}<li>{data.name}</li>{/snippet}`
- **Event**: `<button onclick={() => count++}>Click</button>`

### SvelteKit Patterns
- **Load**: `export const load: PageLoad = async ({ params, fetch }) => { ... }`
- **Action**: `export const actions = { default: async ({ request }) => { ... } }`
- **Store**: `export const users = writable<User[]>([]); const derived = derived(users, $u => ...)`

