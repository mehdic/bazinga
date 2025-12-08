---
name: javascript
type: language
priority: 1
token_estimate: 550
compatible_with: [developer, senior_software_engineer]
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# JavaScript Engineering Expertise

## Specialist Profile
JavaScript specialist building modern applications. Expert in ES6+ features, async patterns, and browser/Node.js runtimes.

---

## Patterns to Follow

### Modern Syntax (ES6+)
- **Arrow functions**: For callbacks and lexical `this` binding
- **Destructuring**: Extract values from objects/arrays cleanly
- **Spread operator**: Clone objects/arrays, merge configurations
- **Template literals**: String interpolation with backticks
- **Optional chaining**: `obj?.prop?.nested` for safe property access
- **Nullish coalescing**: `value ?? defaultValue` (not `||` for falsy values)

### Async Patterns
- **async/await**: Preferred over raw Promises for readability
- **Promise.all**: For parallel operations that can run concurrently
- **Promise.allSettled**: When you need results of all promises, even failures
- **Error boundaries**: Always catch async errors with try/catch

### Functions
- **Pure functions**: Same input = same output, no side effects
- **Default parameters**: `function foo(x = 10)` over manual checks
- **Rest parameters**: `function foo(...args)` for variable arguments
- **Named exports**: Prefer over default exports for better tooling

### Data Handling
- **Immutable updates**: Spread for objects/arrays, not mutation
- **Array methods**: `map`, `filter`, `reduce` over loops when appropriate
- **Object methods**: `Object.entries`, `Object.fromEntries`, `Object.assign`
- **Set and Map**: For unique values and key-value pairs

### Error Handling
- **Custom Error classes**: Extend Error for domain-specific errors
- **Error messages**: Include context (what failed, why, how to fix)
- **Validation at boundaries**: Validate external input (API, user input)

---

## Patterns to Avoid

### Legacy Patterns
- ❌ **`var` keyword**: Use `const` (preferred) or `let`
- ❌ **`==` comparison**: Use strict equality `===`
- ❌ **`arguments` object**: Use rest parameters `...args`
- ❌ **`for...in` for arrays**: Use `for...of` or array methods

### Dangerous Patterns
- ❌ **`eval()`**: Security risk, use alternatives
- ❌ **`with` statement**: Ambiguous scope
- ❌ **Implicit globals**: Always declare variables
- ❌ **Modifying built-in prototypes**: Breaks expectations

### Anti-Patterns
- ❌ **Callback hell**: Use Promises/async-await
- ❌ **Floating promises**: Always await or handle
- ❌ **Synchronous I/O in async context**: Block event loop
- ❌ **Type coercion reliance**: Be explicit about types

### Code Quality Issues
- ❌ **Magic numbers/strings**: Use named constants
- ❌ **Long functions**: Break into smaller, focused functions
- ❌ **Deep nesting**: Early returns, extract functions
- ❌ **Inconsistent naming**: Follow camelCase convention

---

## Verification Checklist

### Code Quality
- [ ] No `var` declarations (use `const`/`let`)
- [ ] Strict equality `===` used throughout
- [ ] All promises are awaited or have error handlers
- [ ] No implicit type coercion

### Error Handling
- [ ] External data validated at boundaries
- [ ] Async errors caught with try/catch
- [ ] Meaningful error messages

### Performance
- [ ] No synchronous operations blocking event loop
- [ ] Arrays not mutated directly (use spread/methods)
- [ ] No memory leaks (event listeners cleaned up)

---

## Code Patterns (Reference)

### Modern Constructs
- **Destructuring**: `const { name, age } = user;`
- **Spread clone**: `const newObj = { ...oldObj, updated: true };`
- **Optional chain**: `const city = user?.address?.city;`
- **Nullish coalesce**: `const value = input ?? 'default';`
- **Array methods**: `items.filter(x => x.active).map(x => x.name)`

### Async Patterns
- **async/await**: `const data = await fetchData();`
- **Parallel**: `const [a, b] = await Promise.all([fetchA(), fetchB()]);`
- **Error handling**: `try { await op(); } catch (err) { handle(err); }`
