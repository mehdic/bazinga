---
name: vue
type: framework
priority: 2
token_estimate: 550
compatible_with: [developer, senior_software_engineer]
requires: [typescript, javascript]
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Vue Engineering Expertise

## Specialist Profile
Vue specialist building reactive applications. Expert in Composition API, Pinia, and Vue 3 ecosystem.

---

## Patterns to Follow

### Composition API
<!-- version: vue >= 3 -->
- **`<script setup>` syntax**: Cleaner, better performance
- **defineProps/defineEmits**: Type-safe props and events
- **ref for primitives**: `ref(0)`, access via `.value`
- **reactive for objects**: `reactive({})`, direct property access
- **computed for derived values**: Cached, reactive computations

### Composables
- **Extract reusable logic**: `useFetch`, `useAuth`, `useForm`
- **Return refs and functions**: Consistent composable API
- **Prefix with `use`**: Convention for composable functions
- **Handle cleanup**: Use `onUnmounted` for side effects
- **Accept refs as arguments**: `MaybeRef<T>` for flexibility

### State Management
- **Pinia for global state**: Type-safe, devtools support
- **Setup store syntax**: Composition API style stores
- **Composables for shared logic**: Not everything needs global state
- **URL state for persistence**: Router query params

### Reactivity
- **toRef/toRefs**: Extract reactive props from objects
- **watchEffect for side effects**: Auto-tracks dependencies
- **watch for specific sources**: Explicit dependency tracking
- **shallowRef for large objects**: When deep reactivity isn't needed

### TypeScript Integration
- **Generic components**: `<script setup lang="ts" generic="T">`
- **Typed props**: Full inference with defineProps
- **Typed emits**: Strong event typing with defineEmits
- **Type-only imports**: `import type { User } from './types'`

---

## Patterns to Avoid

### API Anti-Patterns
- ❌ **Options API for new code**: Use Composition API
- ❌ **Mixing APIs**: Pick one style per component
- ❌ **`this` in Composition API**: No `this` context; use refs
- ❌ **Mutating props directly**: Emit events to parent

### Reactivity Anti-Patterns
- ❌ **Destructuring reactive objects**: Loses reactivity; use toRefs
- ❌ **Deep watchers without need**: Performance cost
- ❌ **Forgetting `.value`**: Refs require `.value` access
- ❌ **Reactive for primitives**: Use ref instead

### State Anti-Patterns
- ❌ **`$refs` for data flow**: Use props/emits or provide/inject
- ❌ **Global mixins**: Hard to track; use composables
- ❌ **Vuex for new projects**: Use Pinia instead
- ❌ **Event bus**: Use provide/inject or Pinia

### Template Anti-Patterns
- ❌ **Complex logic in templates**: Move to computed/methods
- ❌ **v-if with v-for**: v-if has higher priority; causes issues
- ❌ **Missing :key on v-for**: Required for proper diffing
- ❌ **Inline styles over classes**: Use utility classes or CSS

---

## Verification Checklist

### Composition API
- [ ] `<script setup>` syntax used
- [ ] defineProps/defineEmits with TypeScript
- [ ] Computed for derived values
- [ ] Watch/watchEffect with cleanup

### Composables
- [ ] Reusable logic extracted
- [ ] Proper naming convention (`use*`)
- [ ] Cleanup in onUnmounted
- [ ] TypeScript types exported

### State Management
- [ ] Pinia for global state
- [ ] Setup store syntax preferred
- [ ] Actions for async operations
- [ ] Getters for computed state

### Performance
- [ ] Lazy-loaded routes
- [ ] shallowRef for large datasets
- [ ] v-once for static content
- [ ] Keep-alive for cached components

---

## Code Patterns (Reference)

### Recommended Constructs
- **Script setup**: `<script setup lang="ts">const count = ref(0)</script>`
- **Typed props**: `const props = defineProps<{ user: User }>()`
- **Typed emits**: `const emit = defineEmits<{ select: [user: User] }>()`
- **Computed**: `const fullName = computed(() => first.value + ' ' + last.value)`
- **Composable**: `function useUser(id: MaybeRef<string>) { return { user, loading } }`
- **Pinia store**: `export const useUserStore = defineStore('users', () => { ... })`
- **Watch**: `watch(source, (newVal) => { ... }, { immediate: true })`

