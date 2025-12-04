---
name: htmx-alpine
type: framework
priority: 2
token_estimate: 350
compatible_with: [developer, senior_software_engineer]
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# HTMX + Alpine.js Engineering Expertise

## Specialist Profile
Hypermedia specialist building interactive apps without heavy JS frameworks. Expert in HTMX patterns, Alpine.js, and progressive enhancement.

## Implementation Guidelines

### HTMX Basics

```html
<!-- GET request on click -->
<button hx-get="/users" hx-target="#user-list" hx-swap="innerHTML">
  Load Users
</button>

<div id="user-list"></div>

<!-- POST form -->
<form hx-post="/users" hx-target="#user-list" hx-swap="beforeend">
  <input name="email" type="email" required>
  <input name="displayName" required>
  <button type="submit">Create User</button>
</form>
```

### HTMX Patterns

```html
<!-- Infinite scroll -->
<div hx-get="/users?page=2"
     hx-trigger="revealed"
     hx-swap="afterend">
  Loading more...
</div>

<!-- Active search -->
<input type="search"
       name="q"
       hx-get="/search"
       hx-trigger="input changed delay:300ms"
       hx-target="#results">

<!-- Delete with confirmation -->
<button hx-delete="/users/123"
        hx-confirm="Are you sure?"
        hx-target="closest tr"
        hx-swap="outerHTML swap:1s">
  Delete
</button>

<!-- Polling -->
<div hx-get="/notifications"
     hx-trigger="every 30s"
     hx-swap="innerHTML">
</div>
```

### Alpine.js Components

```html
<!-- Toggle -->
<div x-data="{ open: false }">
  <button @click="open = !open">Toggle</button>
  <div x-show="open" x-transition>
    Content here
  </div>
</div>

<!-- Form with validation -->
<form x-data="{ email: '', valid: false }"
      x-effect="valid = email.includes('@')">
  <input type="email" x-model="email">
  <button :disabled="!valid">Submit</button>
</form>

<!-- Fetch data -->
<div x-data="{ users: [] }"
     x-init="users = await (await fetch('/api/users')).json()">
  <template x-for="user in users" :key="user.id">
    <div x-text="user.name"></div>
  </template>
</div>
```

### Combined Patterns

```html
<!-- HTMX + Alpine modal -->
<div x-data="{ showModal: false }">
  <button @click="showModal = true">Open Modal</button>

  <div x-show="showModal" x-transition class="modal">
    <div hx-get="/modal-content"
         hx-trigger="intersect once"
         hx-swap="innerHTML">
      Loading...
    </div>
    <button @click="showModal = false">Close</button>
  </div>
</div>
```

### Server Response Patterns

```python
# Return HTML fragments, not JSON
@app.post("/users")
async def create_user(request: Request):
    user = await create_user_from_form(request)
    return templates.TemplateResponse(
        "partials/user_row.html",
        {"request": request, "user": user}
    )
```

## Patterns to Avoid
- ❌ Over-engineering simple interactions
- ❌ Returning JSON (return HTML)
- ❌ Full page reloads when partials work
- ❌ Complex state in Alpine (use backend)

## Verification Checklist
- [ ] HTML over the wire
- [ ] Progressive enhancement
- [ ] Minimal client-side state
- [ ] Proper loading indicators
- [ ] Accessible interactions
