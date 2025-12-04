---
name: django
type: framework
priority: 2
token_estimate: 600
compatible_with: [developer, senior_software_engineer]
requires: [python]
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Django Engineering Expertise

## Specialist Profile
Django specialist building robust web applications. Expert in ORM, Django REST Framework, and async patterns.

---

## Patterns to Follow

### Model Design
- **UUID primary keys**: Better for distributed systems
- **Explicit indexes**: `models.Index` for query patterns
<!-- version: django >= 3.0 -->
- **Choices as enums**: Use TextChoices/IntegerChoices
<!-- version: django < 3.0 -->
- **Choices as tuples**: `CHOICES = [('A', 'Active'), ('I', 'Inactive')]`
<!-- version: django >= 2.2 -->
- **`auto_now`/`auto_now_add`**: For timestamps
- **Manager methods**: Encapsulate complex queries

### QuerySet Optimization
- **select_related**: For ForeignKey/OneToOne (single query JOIN)
- **prefetch_related**: For reverse ForeignKey/ManyToMany
- **only()/defer()**: Limit fields fetched
- **annotate/aggregate**: Database-level computations
- **bulk operations**: `bulk_create`, `bulk_update`, `update()`

### Django REST Framework
- **Separate serializers per action**: Create vs Read vs Update
- **ViewSets for CRUD**: Less boilerplate
- **Pagination by default**: Always paginate lists
- **Permission classes**: Explicit authorization
- **Throttling**: Rate limiting for public APIs

### Async Support (Django 5+)
<!-- version: django >= 5 -->
- **Async views where beneficial**: `async def view(request)`
- **Async ORM methods**: Use `a` prefix (`aget`, `afilter`, `acount`)
- **async for on querysets**: Iterate asynchronously
- **sync_to_async for blocking**: Wrap sync code properly
- **ASGI deployment**: Required for async benefits

### Service Layer
- **Business logic in services**: Not in views or serializers
- **Transaction boundaries**: `@transaction.atomic` in services
- **Fat models, thin views**: Logic close to data
- **Signals sparingly**: Explicit calls are often clearer

---

## Patterns to Avoid

### ORM Anti-Patterns
- ❌ **N+1 queries**: Always use select_related/prefetch_related
- ❌ **Unindexed filter fields**: Add indexes for query patterns
- ❌ **Querying in loops**: Use bulk operations
- ❌ **`.all()` without pagination**: Memory issues at scale
- ❌ **`save()` in loops**: Use `bulk_update`

### Architecture Anti-Patterns
- ❌ **Fat views**: Move logic to services/models
- ❌ **Business logic in serializers**: Serializers for data transformation only
- ❌ **Signals for business logic**: Hard to debug; use explicit calls
- ❌ **Callbacks everywhere**: Prefer explicit transaction handling

### Async Anti-Patterns
- ❌ **Blocking in async views**: Use `sync_to_async` wrapper
- ❌ **`time.sleep` in async**: Use `asyncio.sleep`
- ❌ **Sync ORM in async view**: Use async ORM methods
- ❌ **WSGI with async views**: Deploy with ASGI

### Security Anti-Patterns
- ❌ **Raw SQL without params**: Use parameterized queries
- ❌ **Skipping validation**: Always validate input
- ❌ **Exposing internal IDs**: Use UUIDs for public APIs

---

## Verification Checklist

### Performance
- [ ] select_related/prefetch_related for relations
- [ ] Indexes on filtered/ordered fields
- [ ] Pagination on all list endpoints
- [ ] No N+1 queries (django-debug-toolbar)

### Architecture
- [ ] Services for business logic
- [ ] Separate serializers per action
- [ ] Migrations are reversible
- [ ] Tests use pytest-django

### DRF
- [ ] ViewSets or generic views
- [ ] Permission classes set
- [ ] Throttling configured
- [ ] OpenAPI schema generated

### Async (if using)
- [ ] ASGI deployment (Uvicorn/Daphne)
- [ ] Async ORM methods used
- [ ] No blocking calls in async views
- [ ] Proper sync_to_async wrapping

---

## Code Patterns (Reference)

### Recommended Constructs
- **Model**: `class User(models.Model): email = models.EmailField(unique=True)`
- **Manager**: `User.objects.active().recent()`
- **QuerySet optimization**: `User.objects.select_related('profile').prefetch_related('orders')`
- **ViewSet**: `class UserViewSet(viewsets.ModelViewSet): queryset = User.objects.all()`
- **Service**: `class UserService: def create(self, data): with transaction.atomic(): ...`
<!-- version: django >= 5 -->
- **Async view**: `async def user_list(request): users = [u async for u in User.objects.all()]`
- **Async ORM**: `user = await User.objects.aget(id=id)`

