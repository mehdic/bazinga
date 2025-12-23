---
name: nextjs
type: framework
priority: 2
token_estimate: 600
compatible_with: [developer, senior_software_engineer]
requires: [typescript, react]
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Next.js Engineering Expertise

## Specialist Profile
Next.js specialist building full-stack React applications. Expert in App Router, Server Components, and Server Actions.

---

## Patterns to Follow

### Server Components
<!-- version: nextjs >= 14 -->
- **Default to server**: Components are Server Components unless marked
- **Data fetching in components**: Fetch where data is needed
- **Async components**: `async function Page()` for server data
- **Small client islands**: Isolate interactivity in imports

### Server Actions
<!-- version: nextjs >= 14 -->
- **Server Actions stable**: Use for mutations without experimental flag
<!-- version: nextjs >= 13, nextjs < 14 -->
- **Server Actions experimental**: Enable `experimental.serverActions` in config
<!-- version: nextjs >= 13.4 -->
- **Mutations via Server Actions**: Not API routes for internal ops
- **Separate actions file**: `'use server'` at module level
- **revalidatePath/revalidateTag**: Update cached data after mutations
- **Error handling**: Return error objects, don't throw to client
- **Input validation**: Never trust form data; validate first

### Caching Strategy
- **Understand defaults**: fetch() is cached by default
- **Explicit cache options**: `cache: 'no-store'` or `revalidate: N`
- **Route segment config**: `export const dynamic = 'force-dynamic'`
- **Tags for granular revalidation**: `next: { tags: ['users'] }`

### File Organization
- **Colocation**: Components near their routes
- **actions/ directory**: Server actions organized separately
- **lib/ for utilities**: Shared code, not route-specific
- **Clear naming**: `updateUserAction`, `submitFormAction`

### Client/Server Boundary
- **Props serialization**: Only send serializable data to client
- **Keep secrets server-side**: Environment variables in server code
- **Minimal client state**: URL state, server state where possible

---

## Patterns to Avoid

### Component Anti-Patterns
- ❌ **`'use client'` everywhere**: Defeats Server Components benefits
- ❌ **Client-side fetch when server works**: Fetch in Server Components
- ❌ **Defining Server Actions in client files**: Must be separate file
- ❌ **Large client components**: Split and isolate interactivity

### Server Action Anti-Patterns
- ❌ **Server Actions for data fetching**: They're for mutations
- ❌ **Calling window/document in actions**: Server-only code
- ❌ **Leaking secrets in errors**: Log server-side, generic to client
- ❌ **No rate limiting**: Add protection for public actions

### Caching Anti-Patterns
- ❌ **Ignoring cache behavior**: Understand when data revalidates
- ❌ **Over-caching dynamic data**: User-specific needs no-store
- ❌ **Forgetting revalidation**: Call after Server Action mutations
- ❌ **redirect() in try/catch**: It throws internally; handle outside

### Architecture Anti-Patterns
- ❌ **API routes for internal data**: Server Actions or Server Components
- ❌ **getServerSideProps/getStaticProps**: App Router patterns instead
- ❌ **Suspense inside async component**: Place higher in tree
- ❌ **pages/ and app/ mixed**: Migrate fully to App Router

---

## Verification Checklist

### Server Components
- [ ] Default server, client only when needed
- [ ] Data fetching at component level
- [ ] Small client islands imported
- [ ] Metadata exported for SEO

### Server Actions
- [ ] Separate file with 'use server'
- [ ] Input validation on all actions
- [ ] revalidatePath/revalidateTag called
- [ ] Errors handled gracefully

### Caching
- [ ] Cache strategy explicit
- [ ] Dynamic routes marked correctly
- [ ] Tags for granular invalidation
- [ ] Sensitive data not cached

### Security
- [ ] Secrets server-side only
- [ ] Rate limiting on actions
- [ ] CSRF protection (built-in for actions)
- [ ] Authorization checks in actions

---

## Code Patterns (Reference)

### Recommended Constructs
<!-- version: nextjs >= 13 -->
- **Server Component**: `async function Page() { const data = await fetch(...); return <div>{data}</div>; }`
- **Client Component**: `'use client'; export function Counter() { const [count, setCount] = useState(0); ... }`
- **Metadata**: `export const metadata = { title: 'Page', description: '...' }`
<!-- version: nextjs >= 13.4 -->
- **Server Action**: `'use server'; export async function createUser(formData: FormData) { ... revalidatePath('/'); }`
- **Caching**: `fetch(url, { next: { revalidate: 60, tags: ['users'] } })`
- **Revalidation**: `revalidateTag('users')` or `revalidatePath('/users')`
- **Dynamic route**: `export const dynamic = 'force-dynamic'` for no-cache routes
<!-- version: nextjs >= 15 -->
- **Async request APIs**: `const params = await props.params` (params/headers now async)
- **fetch no cache default**: `fetch()` is `cache: 'no-store'` by default
<!-- version: nextjs < 13 -->
- **Pages Router**: Use `getServerSideProps`/`getStaticProps` for data fetching
- **API Routes**: Use `pages/api/` for backend endpoints

