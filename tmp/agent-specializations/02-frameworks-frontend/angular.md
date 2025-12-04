---
name: angular
type: framework
priority: 2
token_estimate: 500
compatible_with: [developer, senior_software_engineer]
requires: [typescript]
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Angular Engineering Expertise

## Specialist Profile
Angular specialist building enterprise applications. Expert in RxJS, dependency injection, and Angular architecture.

## Implementation Guidelines

### Standalone Components

<!-- version: angular >= 17 -->
```typescript
@Component({
  selector: 'app-user-card',
  standalone: true,
  imports: [CommonModule],
  template: `
    <article (click)="onSelect()" (keydown.enter)="onSelect()" tabindex="0">
      <h2>{{ user().displayName }}</h2>
      <p>{{ user().email }}</p>
    </article>
  `,
})
export class UserCardComponent {
  user = input.required<User>();
  select = output<User>();

  onSelect() {
    this.select.emit(this.user());
  }
}
```

### Signals

<!-- version: angular >= 17 -->
```typescript
@Component({...})
export class UserListComponent {
  private userService = inject(UserService);

  users = signal<User[]>([]);
  filter = signal('');
  loading = signal(false);

  filteredUsers = computed(() =>
    this.users().filter(u =>
      u.name.toLowerCase().includes(this.filter().toLowerCase())
    )
  );

  constructor() {
    effect(() => {
      console.log(`Showing ${this.filteredUsers().length} users`);
    });
  }

  async loadUsers() {
    this.loading.set(true);
    try {
      this.users.set(await this.userService.getAll());
    } finally {
      this.loading.set(false);
    }
  }
}
```

### Services

```typescript
@Injectable({ providedIn: 'root' })
export class UserService {
  private http = inject(HttpClient);
  private readonly baseUrl = '/api/users';

  getAll(): Observable<User[]> {
    return this.http.get<User[]>(this.baseUrl);
  }

  getById(id: string): Observable<User> {
    return this.http.get<User>(`${this.baseUrl}/${id}`);
  }

  create(request: CreateUserRequest): Observable<User> {
    return this.http.post<User>(this.baseUrl, request);
  }
}
```

### RxJS Patterns

```typescript
// Combine with switchMap for latest
searchUsers$ = this.searchTerm$.pipe(
  debounceTime(300),
  distinctUntilChanged(),
  switchMap(term => this.userService.search(term)),
  catchError(() => of([]))
);

// Handle loading state
loadUser(id: string) {
  this.loading$.next(true);
  return this.userService.getById(id).pipe(
    finalize(() => this.loading$.next(false))
  );
}
```

### Reactive Forms

```typescript
form = this.fb.group({
  email: ['', [Validators.required, Validators.email]],
  displayName: ['', [Validators.required, Validators.minLength(2)]],
});

onSubmit() {
  if (this.form.valid) {
    this.userService.create(this.form.value);
  }
}
```

## Patterns to Avoid
- ❌ Module-based components (use standalone)
- ❌ Constructor injection (use `inject()`)
- ❌ Subscribing without unsubscribing
- ❌ NgModules for new code

## Verification Checklist
- [ ] Standalone components
- [ ] Signals for state
- [ ] `inject()` for DI
- [ ] Proper RxJS cleanup
- [ ] OnPush change detection
