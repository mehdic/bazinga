---
name: vue
type: framework
priority: 2
token_estimate: 500
compatible_with: [developer, senior_software_engineer]
requires: [typescript, javascript]
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Vue Engineering Expertise

## Specialist Profile
Vue specialist building reactive applications. Expert in Composition API, Pinia, and Vue ecosystem.

## Implementation Guidelines

### Composition API

<!-- version: vue >= 3 -->
```vue
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';

interface Props {
  userId: string;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  select: [user: User];
}>();

const user = ref<User | null>(null);
const loading = ref(true);

const displayName = computed(() =>
  user.value?.displayName ?? 'Unknown'
);

onMounted(async () => {
  try {
    user.value = await fetchUser(props.userId);
  } finally {
    loading.value = false;
  }
});

function handleSelect() {
  if (user.value) {
    emit('select', user.value);
  }
}
</script>

<template>
  <div v-if="loading">Loading...</div>
  <article v-else-if="user" @click="handleSelect">
    <h2>{{ displayName }}</h2>
    <p>{{ user.email }}</p>
  </article>
</template>
```

### Composables

```typescript
// composables/useUser.ts
export function useUser(userId: MaybeRef<string>) {
  const user = ref<User | null>(null);
  const loading = ref(false);
  const error = ref<Error | null>(null);

  async function fetch() {
    loading.value = true;
    error.value = null;
    try {
      user.value = await api.getUser(toValue(userId));
    } catch (e) {
      error.value = e as Error;
    } finally {
      loading.value = false;
    }
  }

  watch(() => toValue(userId), fetch, { immediate: true });

  return { user, loading, error, refetch: fetch };
}
```

### Pinia Store

```typescript
// stores/users.ts
export const useUserStore = defineStore('users', () => {
  const users = ref<User[]>([]);
  const selectedId = ref<string | null>(null);

  const selectedUser = computed(() =>
    users.value.find(u => u.id === selectedId.value)
  );

  async function fetchUsers() {
    users.value = await api.getUsers();
  }

  function selectUser(id: string) {
    selectedId.value = id;
  }

  return { users, selectedId, selectedUser, fetchUsers, selectUser };
});
```

### Watchers

```typescript
// Watch with immediate
watch(userId, async (newId) => {
  user.value = await fetchUser(newId);
}, { immediate: true });

// Watch multiple sources
watch([firstName, lastName], ([first, last]) => {
  fullName.value = `${first} ${last}`;
});

// watchEffect for reactive dependencies
watchEffect(() => {
  console.log(`User: ${user.value?.name}`);
});
```

## Patterns to Avoid
- ❌ Options API for new code (use Composition)
- ❌ Mutating props directly
- ❌ Deep watchers without need
- ❌ `$refs` for data flow

## Verification Checklist
- [ ] Composition API with `<script setup>`
- [ ] TypeScript for props/emits
- [ ] Composables for reusable logic
- [ ] Pinia for global state
- [ ] Proper cleanup in onUnmounted
