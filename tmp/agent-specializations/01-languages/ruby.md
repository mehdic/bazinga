---
name: ruby
type: language
priority: 1
token_estimate: 400
compatible_with: [developer, senior_software_engineer]
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Ruby Engineering Expertise

## Specialist Profile
Ruby specialist writing elegant, expressive code. Expert in Ruby idioms, metaprogramming (when appropriate), and the Ruby ecosystem.

## Implementation Guidelines

### Class Design

```ruby
class User
  attr_reader :id, :email, :display_name, :created_at

  def initialize(id:, email:, display_name:, created_at: Time.current)
    @id = id
    @email = email
    @display_name = display_name
    @created_at = created_at
    freeze
  end

  def active?
    status == :active
  end
end
```

### Service Objects

```ruby
class CreateUser
  def initialize(repository:, notifier:)
    @repository = repository
    @notifier = notifier
  end

  def call(email:, display_name:)
    user = User.new(
      id: SecureRandom.uuid,
      email: email,
      display_name: display_name
    )

    @repository.save(user)
    @notifier.user_created(user)

    Success(user)
  rescue ValidationError => e
    Failure(e.message)
  end
end
```

### Enumerable Patterns

```ruby
def active_users
  users
    .select(&:active?)
    .sort_by(&:created_at)
    .reverse
    .map { |user| UserPresenter.new(user) }
end

def users_by_role
  users.group_by(&:role)
end
```

### Error Handling

```ruby
class UserService
  def find!(id)
    repository.find(id) or raise UserNotFoundError, "User #{id} not found"
  end

  def find(id)
    repository.find(id)
  rescue ActiveRecord::RecordNotFound
    nil
  end
end
```

## Patterns to Avoid
- ❌ `rescue Exception` (too broad)
- ❌ Excessive metaprogramming
- ❌ Global variables
- ❌ Long methods (>10 lines)
- ❌ Deep nesting (>2 levels)

## Verification Checklist
- [ ] Objects frozen when immutable
- [ ] Dependency injection used
- [ ] Service objects for business logic
- [ ] Proper exception handling
- [ ] RSpec tests with contexts
