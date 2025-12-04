---
name: react
type: framework
priority: 2
token_estimate: 500
compatible_with: [developer, senior_software_engineer]
requires: [typescript, javascript]
---

> **PRECEDENCE**: Base agent workflow, routing, and reporting rules take precedence over this guidance.

# React Engineering Expertise

## Specialist Profile

React specialist building performant, accessible UIs. Expert in hooks, state management, and component architecture.

## Implementation Guidelines

### Functional Components

<!-- version: react >= 18 -->
```tsx
interface UserCardProps {
  user: User;
  onSelect?: (user: User) => void;
}

export function UserCard({ user, onSelect }: UserCardProps) {
  const handleClick = useCallback(() => {
    onSelect?.(user);
  }, [user, onSelect]);

  return (
    <article className="user-card" onClick={handleClick} role="button" tabIndex={0}>
      <h2>{user.displayName}</h2>
      <p>{user.email}</p>
    </article>
  );
}
```

<!-- version: react >= 16.8, react < 18 -->
```tsx
interface UserCardProps {
  user: User;
  onSelect?: (user: User) => void;
}

export const UserCard: React.FC<UserCardProps> = ({ user, onSelect }) => {
  const handleClick = useCallback(() => {
    onSelect?.(user);
  }, [user, onSelect]);

  return (
    <article className="user-card" onClick={handleClick}>
      <h2>{user.displayName}</h2>
      <p>{user.email}</p>
    </article>
  );
};
```

### Custom Hooks

```tsx
function useAsync<T>(asyncFn: () => Promise<T>, deps: unknown[] = []) {
  const [state, setState] = useState<{
    data: T | null;
    loading: boolean;
    error: Error | null;
  }>({ data: null, loading: true, error: null });

  useEffect(() => {
    let cancelled = false;

    setState(prev => ({ ...prev, loading: true, error: null }));

    asyncFn()
      .then(data => {
        if (!cancelled) {
          setState({ data, loading: false, error: null });
        }
      })
      .catch(error => {
        if (!cancelled) {
          setState({ data: null, loading: false, error });
        }
      });

    return () => {
      cancelled = true;
    };
  }, deps);

  return state;
}

// Usage
function UserProfile({ userId }: { userId: string }) {
  const { data: user, loading, error } = useAsync(
    () => fetchUser(userId),
    [userId]
  );

  if (loading) return <Spinner />;
  if (error) return <ErrorMessage error={error} />;
  return <UserCard user={user!} />;
}
```

### State Management

<!-- version: react >= 18 -->
```tsx
// Using useReducer for complex state
interface State {
  users: User[];
  selectedId: string | null;
  filter: string;
}

type Action =
  | { type: 'SET_USERS'; payload: User[] }
  | { type: 'SELECT_USER'; payload: string }
  | { type: 'SET_FILTER'; payload: string };

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'SET_USERS':
      return { ...state, users: action.payload };
    case 'SELECT_USER':
      return { ...state, selectedId: action.payload };
    case 'SET_FILTER':
      return { ...state, filter: action.payload };
    default:
      return state;
  }
}

function UserList() {
  const [state, dispatch] = useReducer(reducer, {
    users: [],
    selectedId: null,
    filter: '',
  });

  const filteredUsers = useMemo(
    () => state.users.filter(u =>
      u.displayName.toLowerCase().includes(state.filter.toLowerCase())
    ),
    [state.users, state.filter]
  );

  return (
    <>
      <SearchInput
        value={state.filter}
        onChange={value => dispatch({ type: 'SET_FILTER', payload: value })}
      />
      {filteredUsers.map(user => (
        <UserCard
          key={user.id}
          user={user}
          onSelect={() => dispatch({ type: 'SELECT_USER', payload: user.id })}
        />
      ))}
    </>
  );
}
```

### Performance Optimization

```tsx
// Memoize expensive components
const MemoizedUserCard = memo(UserCard, (prev, next) =>
  prev.user.id === next.user.id
);

// Memoize callbacks
const handleSubmit = useCallback((data: FormData) => {
  onSubmit(data);
}, [onSubmit]);

// Memoize computed values
const sortedUsers = useMemo(
  () => [...users].sort((a, b) => a.displayName.localeCompare(b.displayName)),
  [users]
);
```

### Error Boundaries

```tsx
interface ErrorBoundaryProps {
  fallback: React.ReactNode;
  children: React.ReactNode;
}

class ErrorBoundary extends React.Component<
  ErrorBoundaryProps,
  { hasError: boolean }
> {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('Error caught:', error, info);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback;
    }
    return this.props.children;
  }
}
```

### Accessibility

```tsx
function Dialog({ isOpen, onClose, title, children }: DialogProps) {
  const dialogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      dialogRef.current?.focus();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div
      ref={dialogRef}
      role="dialog"
      aria-modal="true"
      aria-labelledby="dialog-title"
      tabIndex={-1}
      onKeyDown={e => e.key === 'Escape' && onClose()}
    >
      <h2 id="dialog-title">{title}</h2>
      {children}
      <button onClick={onClose}>Close</button>
    </div>
  );
}
```

## Patterns to Avoid

- Class components for new code (use hooks)
- Inline object/array creation in JSX (causes re-renders)
- Missing `key` props in lists
- State updates in useEffect without cleanup
- Direct DOM manipulation
- Prop drilling > 3 levels (use context)
<!-- version: react < 16.8 -->
- N/A: Hooks (React 16.8+ only)

## Verification Checklist

- [ ] Proper TypeScript types for props
- [ ] Memoization for expensive computations
- [ ] useCallback for event handlers passed as props
- [ ] Cleanup functions in useEffect
- [ ] Keyboard accessibility
- [ ] ARIA attributes for interactive elements
- [ ] Error boundaries around fallible components
