---
name: astro
type: framework
priority: 2
token_estimate: 550
compatible_with: [developer, senior_software_engineer]
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Astro Engineering Expertise

## Specialist Profile
Astro specialist building fast, content-focused sites. Expert in islands architecture, Content Collections, and zero-JS-by-default.

---

## Patterns to Follow

### Islands Architecture
- **Zero JS by default**: Static HTML unless hydration needed
- **Client directives**: Choose hydration strategy per component
- **`client:load`**: Interactive immediately (use sparingly)
- **`client:visible`**: Hydrate when scrolled into view
- **`client:idle`**: Hydrate when browser is idle
- **`client:media`**: Hydrate on media query match

### Server Islands (Astro 5+)
<!-- version: astro >= 5 -->
- **`server:defer`**: Dynamic content rendered separately
- **Personalization**: User-specific without blocking static
- **Real-time data**: Prices, inventory, recommendations
- **Performance**: Static shell with dynamic islands

### Content Collections
- **Typed schemas**: Zod validation for frontmatter
- **Content Layer API**: Multiple data sources (local, CMS, API)
- **Type-safe queries**: `getCollection()`, `getEntry()`
- **Build-time validation**: Catch errors early

### Performance
- **Default SSG**: Pre-render when possible
- **Image optimization**: `<Image>` component
- **View transitions**: Smooth page navigation
- **Prefetching**: `data-astro-prefetch` for instant loads

### Multi-Framework
- **Mix frameworks**: React, Vue, Svelte, Solid in same project
- **Share state**: Nano Stores for cross-framework state
- **Pick per-component**: Best tool for each job
- **Consistent styling**: Tailwind or CSS across all

---

## Patterns to Avoid

### Hydration Anti-Patterns
- ❌ **`client:load` everywhere**: Ships unnecessary JS
- ❌ **Interactive framework for static content**: Use Astro components
- ❌ **Heavy JS on content pages**: Islands should be small
- ❌ **Hydrating above-fold unnecessarily**: Start with static

### Architecture Anti-Patterns
- ❌ **SSR when SSG works**: Pre-render for performance
- ❌ **Ignoring Content Collections**: Type-safe content is better
- ❌ **Client-side routing for content sites**: MPA is fine
- ❌ **Complex state management**: Backend for complexity

### Content Anti-Patterns
- ❌ **Untyped frontmatter**: Define schemas with Zod
- ❌ **Fetching at runtime when build-time works**: SSG advantage
- ❌ **Large markdown files**: Split into collections
- ❌ **Missing image optimization**: Use `<Image>` component

### Performance Anti-Patterns
- ❌ **Blocking third-party scripts**: Defer or async
- ❌ **Skipping prefetch**: Use for predictable navigation
- ❌ **No View Transitions**: Smooth UX for multi-page
- ❌ **Unoptimized images**: Astro handles this; use it

---

## Verification Checklist

### Performance
- [ ] Zero JS default verified
- [ ] Appropriate client directives
- [ ] Images optimized
- [ ] Lighthouse score checked

### Content
- [ ] Content Collections with schemas
- [ ] Frontmatter validated
- [ ] Type-safe queries used
- [ ] Draft/published handling

### Architecture
- [ ] SSG where possible
- [ ] Islands for interactivity only
- [ ] Minimal framework code shipped
- [ ] View transitions configured

### SEO
- [ ] Metadata on all pages
- [ ] Sitemap generated
- [ ] robots.txt configured
- [ ] OpenGraph/Twitter cards

---

## Code Patterns (Reference)

### Recommended Constructs
- **Astro component**: `---\nconst { title } = Astro.props;\n---\n<h1>{title}</h1>`
- **Client directive**: `<Counter client:visible />`
- **Content Collection**: `const posts = await getCollection('blog', ({ data }) => !data.draft)`
<!-- version: astro >= 5 -->
- **Server island**: `<UserAvatar server:defer />`
- **Content schema**: `const blog = defineCollection({ schema: z.object({ title: z.string() }) })`
- **Image**: `<Image src={import('./hero.jpg')} alt="..." width={800} />`
- **View transition**: `<ViewTransitions />` in layout head

