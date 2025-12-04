---
name: laravel
type: framework
priority: 2
token_estimate: 450
compatible_with: [developer, senior_software_engineer]
requires: [php]
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Laravel Engineering Expertise

## Specialist Profile
Laravel specialist building PHP web applications. Expert in Eloquent, service container, and Laravel ecosystem.

## Implementation Guidelines

### Models

```php
class User extends Model
{
    protected $fillable = ['email', 'display_name', 'status'];

    protected $casts = [
        'email_verified_at' => 'datetime',
        'status' => UserStatus::class,
    ];

    // Relationships
    public function orders(): HasMany
    {
        return $this->hasMany(Order::class);
    }

    public function profile(): HasOne
    {
        return $this->hasOne(Profile::class);
    }

    // Scopes
    public function scopeActive(Builder $query): Builder
    {
        return $query->where('status', UserStatus::Active);
    }

    public function scopeRecent(Builder $query): Builder
    {
        return $query->orderByDesc('created_at');
    }

    // Accessors
    protected function displayName(): Attribute
    {
        return Attribute::make(
            get: fn (string $value) => ucfirst($value),
        );
    }
}
```

### Controllers

```php
class UserController extends Controller
{
    public function __construct(
        private readonly UserService $userService,
    ) {}

    public function index(IndexUsersRequest $request): AnonymousResourceCollection
    {
        $users = $this->userService->list($request->validated());
        return UserResource::collection($users);
    }

    public function store(StoreUserRequest $request): UserResource
    {
        $user = $this->userService->create($request->validated());
        return new UserResource($user);
    }

    public function show(User $user): UserResource
    {
        return new UserResource($user->load(['profile', 'orders']));
    }
}
```

### Form Requests

```php
class StoreUserRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true;
    }

    public function rules(): array
    {
        return [
            'email' => ['required', 'email', 'unique:users'],
            'display_name' => ['required', 'string', 'min:2', 'max:100'],
        ];
    }

    public function messages(): array
    {
        return [
            'email.unique' => 'This email is already registered.',
        ];
    }
}
```

### Services

```php
class UserService
{
    public function __construct(
        private readonly UserRepository $repository,
        private readonly NotificationService $notifier,
    ) {}

    public function create(array $data): User
    {
        return DB::transaction(function () use ($data) {
            $user = $this->repository->create($data);

            Profile::create(['user_id' => $user->id]);

            $this->notifier->sendWelcome($user);

            return $user;
        });
    }

    public function list(array $filters): LengthAwarePaginator
    {
        return User::query()
            ->when($filters['status'] ?? null, fn ($q, $s) => $q->where('status', $s))
            ->active()
            ->recent()
            ->paginate($filters['per_page'] ?? 15);
    }
}
```

### API Resources

```php
class UserResource extends JsonResource
{
    public function toArray(Request $request): array
    {
        return [
            'id' => $this->id,
            'email' => $this->email,
            'display_name' => $this->display_name,
            'status' => $this->status,
            'profile' => new ProfileResource($this->whenLoaded('profile')),
            'created_at' => $this->created_at->toIso8601String(),
        ];
    }
}
```

## Patterns to Avoid
- ❌ Logic in controllers (use services)
- ❌ N+1 queries (use eager loading)
- ❌ Manual validation in controllers
- ❌ Raw queries without bindings

## Verification Checklist
- [ ] Form Requests for validation
- [ ] API Resources for responses
- [ ] Services for business logic
- [ ] Eager loading relationships
- [ ] Feature tests with RefreshDatabase
