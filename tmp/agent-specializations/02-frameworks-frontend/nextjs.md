---
name: nextjs
type: framework
priority: 2
token_estimate: 550
compatible_with: [developer, senior_software_engineer]
requires: [typescript, react]
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Next.js Engineering Expertise

## Specialist Profile
Next.js specialist building full-stack React applications. Expert in App Router, Server Components, and data fetching.

## Implementation Guidelines

### Server Components

<!-- version: nextjs >= 14 -->
```tsx
// app/users/page.tsx (Server Component by default)
import { getUsers } from '@/lib/users';

export default async function UsersPage() {
  const users = await getUsers();

  return (
    <main>
      <h1>Users</h1>
      <UserList users={users} />
    </main>
  );
}

// Metadata
export const metadata = {
  title: 'Users',
  description: 'View all users',
};
```

### Client Components

```tsx
'use client';

import { useState, useTransition } from 'react';
import { createUser } from '@/app/actions';

export function CreateUserForm() {
  const [isPending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(formData: FormData) {
    startTransition(async () => {
      const result = await createUser(formData);
      if (result.error) setError(result.error);
    });
  }

  return (
    <form action={handleSubmit}>
      <input name="email" type="email" required />
      <input name="displayName" required />
      <button disabled={isPending}>
        {isPending ? 'Creating...' : 'Create User'}
      </button>
      {error && <p className="error">{error}</p>}
    </form>
  );
}
```

### Server Actions

```typescript
// app/actions.ts
'use server';

import { revalidatePath } from 'next/cache';
import { redirect } from 'next/navigation';

export async function createUser(formData: FormData) {
  const email = formData.get('email') as string;
  const displayName = formData.get('displayName') as string;

  try {
    await db.users.create({ email, displayName });
    revalidatePath('/users');
    redirect('/users');
  } catch (error) {
    return { error: 'Failed to create user' };
  }
}
```

### Data Fetching

```typescript
// With caching
async function getUser(id: string) {
  const res = await fetch(`${API_URL}/users/${id}`, {
    next: { revalidate: 60 }, // Revalidate every 60s
  });
  return res.json();
}

// No caching
async function getCurrentUser() {
  const res = await fetch(`${API_URL}/me`, {
    cache: 'no-store',
  });
  return res.json();
}
```

### Route Handlers

```typescript
// app/api/users/route.ts
import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const status = searchParams.get('status');

  const users = await db.users.findMany({
    where: status ? { status } : undefined,
  });

  return NextResponse.json(users);
}

export async function POST(request: NextRequest) {
  const body = await request.json();
  const user = await db.users.create({ data: body });
  return NextResponse.json(user, { status: 201 });
}
```

## Patterns to Avoid
- ❌ `'use client'` on everything
- ❌ Client-side data fetching when server works
- ❌ getServerSideProps (use App Router)
- ❌ API routes for internal data (use Server Actions)

## Verification Checklist
- [ ] Server Components by default
- [ ] Client Components only when needed
- [ ] Server Actions for mutations
- [ ] Proper caching strategy
- [ ] Metadata for SEO
