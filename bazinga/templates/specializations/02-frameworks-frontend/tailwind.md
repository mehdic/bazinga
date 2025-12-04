---
name: tailwind
type: framework
priority: 2
token_estimate: 500
compatible_with: [developer, senior_software_engineer]
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Tailwind CSS Engineering Expertise

## Specialist Profile
Tailwind specialist building consistent, responsive UIs. Expert in utility-first CSS, design systems, and component patterns.

---

## Patterns to Follow

### Utility-First Approach
- **Utilities over custom CSS**: Build UIs entirely with utilities
- **Design constraints**: Use the spacing/color scale, not arbitrary values
- **Semantic colors**: Define brand/semantic colors in config
- **Component abstractions**: Combine utilities in reusable components

### Tailwind v4 Patterns
<!-- version: tailwind >= 4 -->
- **CSS-first configuration**: `@theme` for design tokens
- **CSS layers**: `@layer theme, base, components, utilities`
- **Native CSS variables**: `--color-brand-500`
- **No preprocessors needed**: Drop Sass/Less/Stylus

### Class Organization
- **Consistent order**: Layout → sizing → spacing → typography → colors → effects
- **Prettier plugin**: Auto-sort classes with official plugin
- **Logical grouping**: Keep related utilities together
- **Line breaks for long lists**: Readable multi-line classes

### Responsive Design
- **Mobile-first**: Default styles for mobile, breakpoint for larger
- **Breakpoint prefixes**: `sm:`, `md:`, `lg:`, `xl:`, `2xl:`
- **Container queries**: `@container` for component-relative sizing
- **Consistent breakpoints**: Use the default scale

### Dark Mode
- **`dark:` variant**: Toggle with class or media preference
- **Semantic tokens**: Define light/dark in config
- **Consistent contrast**: Test both modes for accessibility
- **System preference**: `prefers-color-scheme` support

---

## Patterns to Avoid

### Configuration Anti-Patterns
- ❌ **Arbitrary values everywhere**: Use design tokens from config
- ❌ **Default color palette in production**: Define semantic colors
- ❌ **Magic numbers**: `w-[437px]` loses design system benefits
- ❌ **Sass/Less/Stylus with v4**: Use native CSS features

### Styling Anti-Patterns
- ❌ **Overusing @apply**: Reduces single-source-of-truth benefit
- ❌ **Custom classes in @layer components (v4)**: Variants won't work
- ❌ **!important overrides**: Rethink the cascade
- ❌ **Mixing Tailwind with vanilla CSS**: Pick one approach

### Architecture Anti-Patterns
- ❌ **Utility classes in plain HTML at scale**: Use component framework
- ❌ **Duplicating class strings**: Extract to components
- ❌ **Inconsistent spacing**: Stick to the scale
- ❌ **No design system**: Define colors, spacing, typography first

### Accessibility Anti-Patterns
- ❌ **Low contrast colors**: Test with contrast checkers
- ❌ **Focus states removed**: Keep or enhance `focus:` styles
- ❌ **Motion without reduced-motion**: Use `motion-safe:`, `motion-reduce:`

---

## Verification Checklist

### Design System
- [ ] Semantic colors defined in config
- [ ] Consistent spacing scale used
- [ ] Typography scale configured
- [ ] No arbitrary magic numbers

### Responsiveness
- [ ] Mobile-first approach
- [ ] All breakpoints tested
- [ ] Container queries where appropriate
- [ ] Touch targets sized correctly

### Accessibility
- [ ] Color contrast passes WCAG
- [ ] Focus states visible
- [ ] reduced-motion respected
- [ ] Dark mode tested

### Code Quality
- [ ] Prettier plugin for class sorting
- [ ] Component abstractions for reuse
- [ ] No @apply overuse
- [ ] Consistent class organization

---

## Code Patterns (Reference)

### Recommended Constructs
- **Responsive**: `<div class="p-4 md:p-6 lg:p-8">...</div>`
- **Dark mode**: `<div class="bg-white dark:bg-gray-900">...</div>`
- **Interactive**: `<button class="bg-blue-600 hover:bg-blue-700 focus:ring-2">...</button>`
- **Layout**: `<div class="flex flex-col gap-4 sm:flex-row">...</div>`
- **Typography**: `<p class="text-sm text-gray-600 dark:text-gray-400">...</p>`
<!-- version: tailwind >= 4 -->
- **Theme token**: `@theme { --color-brand: #0ea5e9; }`
- **Container query**: `<div class="@container"><div class="@md:flex">...</div></div>`

