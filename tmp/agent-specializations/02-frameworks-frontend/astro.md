---
name: astro
type: framework
priority: 2
token_estimate: 400
compatible_with: [developer, senior_software_engineer]
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Astro Engineering Expertise

## Specialist Profile
Astro specialist building fast, content-focused sites. Expert in islands architecture, content collections, and SSG/SSR.

## Implementation Guidelines

### Astro Components

```astro
---
// src/components/UserCard.astro
interface Props {
  user: User;
  showEmail?: boolean;
}

const { user, showEmail = false } = Astro.props;
---

<article class="user-card">
  <h2>{user.displayName}</h2>
  {showEmail && <p>{user.email}</p>}
  <slot />
</article>

<style>
  .user-card {
    padding: 1rem;
    border-radius: 0.5rem;
    background: var(--card-bg);
  }
</style>
```

### Islands (Client Hydration)

```astro
---
import Counter from '../components/Counter.tsx';
import Newsletter from '../components/Newsletter.vue';
---

<!-- No JS shipped -->
<UserCard user={user} />

<!-- Hydrate on load -->
<Counter client:load initialCount={5} />

<!-- Hydrate when visible -->
<Newsletter client:visible />

<!-- Hydrate on idle -->
<Comments client:idle />

<!-- Hydrate on media query -->
<MobileMenu client:media="(max-width: 768px)" />
```

### Content Collections

```typescript
// src/content/config.ts
import { z, defineCollection } from 'astro:content';

const blog = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    publishDate: z.date(),
    author: z.string(),
    tags: z.array(z.string()),
    draft: z.boolean().default(false),
  }),
});

export const collections = { blog };
```

```astro
---
// src/pages/blog/[...slug].astro
import { getCollection } from 'astro:content';

export async function getStaticPaths() {
  const posts = await getCollection('blog', ({ data }) => !data.draft);
  return posts.map(post => ({
    params: { slug: post.slug },
    props: { post },
  }));
}

const { post } = Astro.props;
const { Content } = await post.render();
---

<article>
  <h1>{post.data.title}</h1>
  <Content />
</article>
```

### API Endpoints

```typescript
// src/pages/api/users.ts
import type { APIRoute } from 'astro';

export const GET: APIRoute = async ({ request }) => {
  const users = await db.users.findMany();
  return new Response(JSON.stringify(users), {
    headers: { 'Content-Type': 'application/json' },
  });
};

export const POST: APIRoute = async ({ request }) => {
  const body = await request.json();
  const user = await db.users.create({ data: body });
  return new Response(JSON.stringify(user), { status: 201 });
};
```

## Patterns to Avoid
- ❌ `client:load` on everything
- ❌ Heavy JS in static pages
- ❌ Ignoring content collections for content sites
- ❌ SSR when SSG works

## Verification Checklist
- [ ] Zero JS by default
- [ ] Appropriate hydration directives
- [ ] Content collections for content
- [ ] Proper image optimization
- [ ] View transitions where appropriate
