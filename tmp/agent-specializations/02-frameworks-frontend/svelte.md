---
name: svelte
type: framework
priority: 2
token_estimate: 400
compatible_with: [developer, senior_software_engineer]
requires: [typescript, javascript]
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Svelte Engineering Expertise

## Specialist Profile
Svelte specialist building reactive, compiled applications. Expert in Svelte 5 runes, stores, and SvelteKit.

## Implementation Guidelines

### Components with Runes

<!-- version: svelte >= 5 -->
```svelte
<script lang="ts">
  interface Props {
    user: User;
    onselect?: (user: User) => void;
  }

  let { user, onselect }: Props = $props();

  let count = $state(0);
  let doubled = $derived(count * 2);

  function handleClick() {
    onselect?.(user);
  }

  $effect(() => {
    console.log(`Count is ${count}`);
  });
</script>

<article onclick={handleClick}>
  <h2>{user.displayName}</h2>
  <p>{user.email}</p>
  <button onclick={() => count++}>
    Clicks: {count} (doubled: {doubled})
  </button>
</article>
```

### Stores

```typescript
// stores/users.ts
import { writable, derived } from 'svelte/store';

function createUserStore() {
  const { subscribe, set, update } = writable<User[]>([]);

  return {
    subscribe,
    async fetch() {
      const users = await api.getUsers();
      set(users);
    },
    add(user: User) {
      update(users => [...users, user]);
    },
    remove(id: string) {
      update(users => users.filter(u => u.id !== id));
    },
  };
}

export const users = createUserStore();

export const activeUsers = derived(users, $users =>
  $users.filter(u => u.status === 'active')
);
```

### Reactive Declarations

<!-- version: svelte < 5 -->
```svelte
<script lang="ts">
  export let items: Item[];
  export let filter: string;

  $: filteredItems = items.filter(i =>
    i.name.toLowerCase().includes(filter.toLowerCase())
  );

  $: itemCount = filteredItems.length;

  $: if (itemCount === 0) {
    console.log('No items match filter');
  }
</script>
```

### Event Handling

```svelte
<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  const dispatch = createEventDispatcher<{
    select: User;
    delete: string;
  }>();

  function handleSelect(user: User) {
    dispatch('select', user);
  }
</script>

<button on:click={() => handleSelect(user)}>
  Select
</button>
```

### SvelteKit Load Functions

```typescript
// +page.ts
export const load: PageLoad = async ({ params, fetch }) => {
  const response = await fetch(`/api/users/${params.id}`);
  const user = await response.json();
  return { user };
};
```

## Patterns to Avoid
- ❌ Complex logic in templates
- ❌ Mutating store values directly
- ❌ Ignoring TypeScript
- ❌ Heavy computation without $derived

## Verification Checklist
- [ ] Runes for Svelte 5+
- [ ] TypeScript props
- [ ] Stores for shared state
- [ ] Event dispatchers typed
- [ ] SvelteKit for routing
