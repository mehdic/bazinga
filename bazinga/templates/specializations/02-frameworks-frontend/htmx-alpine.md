---
name: htmx-alpine
type: framework
priority: 2
token_estimate: 500
compatible_with: [developer, senior_software_engineer]
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# HTMX + Alpine.js Engineering Expertise

## Specialist Profile
Hypermedia specialist building interactive apps without heavy JS frameworks. Expert in HTMX patterns, Alpine.js, and progressive enhancement.

---

## Patterns to Follow

### HTMX Fundamentals
- **HTML over the wire**: Return HTML fragments, not JSON
- **hx-get/hx-post**: AJAX requests with simple attributes
- **hx-target**: Specify where response goes
- **hx-swap**: Control how content is inserted
- **hx-trigger**: Customize when requests fire

### HTMX Patterns
- **Active search**: `hx-trigger="input changed delay:300ms"`
- **Infinite scroll**: `hx-trigger="revealed"`
- **Polling**: `hx-trigger="every 30s"`
- **Confirmation**: `hx-confirm="Are you sure?"`
- **Loading indicators**: `hx-indicator` with CSS transitions
<!-- version: htmx >= 1.9 -->
- **hx-on for events**: `hx-on:click="alert('clicked')"` inline handlers
- **htmx.ajax()**: Programmatic HTMX requests
<!-- version: htmx >= 2.0 -->
- **htmx: prefix events**: Events now prefixed (htmx:afterSwap vs afterSwap.htmx)
- **Deprecated removals**: Some 1.x deprecated features removed

### Alpine.js Integration
- **Client-only interactivity**: Dropdowns, modals, tabs
- **x-data for state**: Local component state
- **x-show/x-if**: Conditional rendering
- **x-transition**: Smooth animations
- **Complement HTMX**: Alpine for UI, HTMX for data
<!-- version: alpine >= 3.0 -->
- **x-bind shorthand**: `:class` instead of `x-bind:class`
- **x-id for unique IDs**: `x-id="['input', 'label']"` generates unique IDs
- **$persist plugin**: Persist state to localStorage
<!-- version: alpine >= 3.10 -->
- **x-teleport**: Move elements to different DOM location

### Server-Side Patterns
- **Return HTML partials**: Not full pages, not JSON
- **Template fragments**: Render just the updated section
- **Proper HTTP verbs**: GET for reads, POST/PUT/DELETE for writes
- **Status codes**: Use 4xx/5xx for errors

### Hypermedia Architecture
- **Locality of behavior**: Logic embedded in HTML
- **Progressive enhancement**: Works without JS
- **Server as source of truth**: Minimal client state
- **Declarative over imperative**: Attributes over scripts

---

## Patterns to Avoid

### HTMX Anti-Patterns
- ❌ **Returning JSON**: HTMX expects HTML
- ❌ **Full page responses for partials**: Return only needed HTML
- ❌ **Complex client state**: Keep state server-side
- ❌ **Missing hx-target**: Response replaces wrong element
- ❌ **Ignoring HTTP semantics**: Use proper verbs/status codes

### Alpine.js Anti-Patterns
- ❌ **Complex business logic**: Move to server
- ❌ **API calls in Alpine**: Use HTMX for server communication
- ❌ **Global state management**: Keep state local or server-side
- ❌ **Over-engineering simple interactions**: Keep it minimal

### Architecture Anti-Patterns
- ❌ **Building SPA with HTMX**: Use React/Vue for complex SPAs
- ❌ **Client-side routing**: HTMX is for hypermedia, not SPAs
- ❌ **REST API + HTMX frontend**: Hypermedia API pattern instead
- ❌ **Ignoring progressive enhancement**: Should work without JS

### Security Anti-Patterns
- ❌ **Missing CSRF protection**: Validate tokens
- ❌ **Unescaped user content**: Server-side escaping required
- ❌ **Trusting client data**: Validate everything server-side

---

## Verification Checklist

### HTMX
- [ ] HTML fragments returned, not JSON
- [ ] Proper hx-target on all triggers
- [ ] Loading indicators configured
- [ ] Error states handled (hx-trigger="htmx:responseError")

### Alpine.js
- [ ] Client-only interactivity
- [ ] No API calls from Alpine
- [ ] Local state only
- [ ] Transitions for UX polish

### Server
- [ ] Partial templates ready
- [ ] Proper HTTP verbs used
- [ ] Status codes meaningful
- [ ] CSRF protection enabled

### Progressive Enhancement
- [ ] Works without JavaScript
- [ ] Core functionality server-rendered
- [ ] Enhanced with HTMX/Alpine
- [ ] Accessibility maintained

---

## Code Patterns (Reference)

### HTMX Constructs
- **Basic request**: `<button hx-get="/users" hx-target="#list">Load</button>`
- **Form submit**: `<form hx-post="/users" hx-target="#list" hx-swap="beforeend">...</form>`
- **Search**: `<input hx-get="/search" hx-trigger="input changed delay:300ms" hx-target="#results">`
- **Delete**: `<button hx-delete="/users/1" hx-target="closest tr" hx-confirm="Delete?">X</button>`
- **Polling**: `<div hx-get="/notifications" hx-trigger="every 30s">...</div>`

### Alpine.js Constructs
- **Toggle**: `<div x-data="{ open: false }"><button @click="open = !open">Toggle</button><div x-show="open">...</div></div>`
- **Dropdown**: `<div x-data="{ open: false }" @click.outside="open = false">...</div>`
- **Form validation**: `<form x-data="{ valid: false }" x-effect="valid = email.includes('@')">...</form>`

### Combined Patterns
- **Modal with HTMX content**: Alpine for show/hide, HTMX for loading content
- **Tabs with server content**: Alpine for tab state, HTMX for lazy-loaded panels

