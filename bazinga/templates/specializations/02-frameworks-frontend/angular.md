---
name: angular
type: framework
priority: 2
token_estimate: 600
compatible_with: [developer, senior_software_engineer]
requires: [typescript]
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Angular Engineering Expertise

## Specialist Profile
Angular specialist building enterprise applications. Expert in Signals, standalone components, and reactive patterns.

---

## Patterns to Follow

### Standalone Components
<!-- version: angular >= 17 -->
- **Standalone by default**: No NgModules for new code
- **`strictStandalone` flag**: Enforce in angularCompilerOptions
- **Direct imports**: Import dependencies in component decorator
- **Lazy loading**: Route-based code splitting

### Signals
<!-- version: angular >= 17 -->
- **signal() for state**: Fine-grained reactivity
- **computed() for derived**: Auto-updating computed values
- **effect() for side effects**: React to signal changes
- **input()/output()**: Signal-based component I/O
- **linkedSignal()**: State that resets based on dependencies

### Dependency Injection
- **inject() function**: Preferred over constructor injection
- **providedIn: 'root'**: Singleton services
- **Injection tokens**: For non-class dependencies
- **Hierarchical injectors**: Scope services to components

### Change Detection
- **OnPush strategy**: Default for all components
- **Signal-based**: Signals enable zoneless change detection
- **Immutable data**: Helps OnPush detect changes
- **Avoid ChangeDetectorRef.detectChanges()**: Design patterns instead

### RxJS Integration
- **Signals for synchronous state**: RxJS for async streams
- **toSignal/toObservable**: Convert between paradigms
- **switchMap for latest**: Cancel previous requests
- **takeUntilDestroyed**: Automatic cleanup
- **shareReplay for caching**: Share subscriptions

---

## Patterns to Avoid

### Module Anti-Patterns
- ❌ **NgModules for new code**: Use standalone components
- ❌ **SharedModule pattern**: Direct imports are clearer
- ❌ **CoreModule pattern**: Use providedIn: 'root'
- ❌ **Feature modules**: Route-based lazy loading instead

### Signal Anti-Patterns
- ❌ **Mixing signals and Zone.js**: Prepare for zoneless
- ❌ **effect() for derived state**: Use computed() instead
- ❌ **Mutable state updates**: Use signal.update() immutably
- ❌ **Ignoring signal warnings**: They indicate migration issues

### RxJS Anti-Patterns
- ❌ **Nested subscriptions**: Use higher-order operators
- ❌ **Forgetting to unsubscribe**: Use takeUntilDestroyed
- ❌ **subscribe() in templates**: Use async pipe or toSignal
- ❌ **subscribe() for side effects only**: Use tap in pipe

### Injection Anti-Patterns
- ❌ **Constructor injection**: Use inject() function
- ❌ **Service in component**: Make services injectable
- ❌ **Static methods on services**: Inject instance instead
- ❌ **Circular dependencies**: Restructure services

### Template Anti-Patterns
- ❌ **Function calls in templates**: Use computed signals
- ❌ **Complex expressions**: Move to component
- ❌ **Unused standalone imports**: Extended diagnostics catch this
- ❌ **Uninvoked functions in bindings**: Missing parentheses

---

## Verification Checklist

### Modern Angular
- [ ] Standalone components only
- [ ] Signals for state management
- [ ] inject() for DI
- [ ] OnPush change detection
- [ ] Prepared for zoneless

### Signals
- [ ] signal() for mutable state
- [ ] computed() for derived values
- [ ] effect() sparingly for side effects
- [ ] input.required() for required inputs

### RxJS
- [ ] No nested subscriptions
- [ ] takeUntilDestroyed for cleanup
- [ ] Higher-order operators used
- [ ] async pipe or toSignal in templates

### Architecture
- [ ] Feature-based organization
- [ ] Smart/dumb component split
- [ ] Services for business logic
- [ ] Route-based lazy loading

---

## Code Patterns (Reference)

### Recommended Constructs
- **Standalone component**: `@Component({ standalone: true, imports: [...] })`
- **Signal**: `count = signal(0); doubled = computed(() => this.count() * 2);`
- **Input**: `user = input.required<User>(); select = output<User>();`
- **Inject**: `private userService = inject(UserService);`
- **Effect**: `effect(() => console.log(this.count()));`
- **toSignal**: `users = toSignal(this.userService.getAll());`
- **takeUntilDestroyed**: `obs$.pipe(takeUntilDestroyed()).subscribe(...)`
<!-- version: angular >= 19 -->
- **linkedSignal**: `selectedId = linkedSignal(() => this.items()[0]?.id)`
- **resource()**: Async data loading with loading/error state

