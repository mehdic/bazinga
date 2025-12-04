---
name: rails
type: framework
priority: 2
token_estimate: 600
compatible_with: [developer, senior_software_engineer]
requires: [ruby]
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Ruby on Rails Engineering Expertise

## Specialist Profile
Rails specialist building rapid web applications. Expert in ActiveRecord, service objects, and Hotwire.

---

## Patterns to Follow

### Model Design
- **Validations in models**: `validates :email, presence: true, uniqueness: true`
- **Scopes for queries**: Named, chainable query methods
- **Enums with prefix**: `enum status: {...}, _prefix: true`
- **Concerns for shared behavior**: Extract reusable modules
- **Associations with dependent**: `has_many :orders, dependent: :destroy`

### Service Objects
- **Single responsibility**: One public method (`call`)
- **Return value objects**: `Success(data)` or `Failure(error)`
- **Explicit dependencies**: Inject via constructor
- **Transaction handling**: Wrap related operations
- **Naming convention**: Verb-noun (`Users::Create`, `Orders::Process`)

### ActiveRecord Optimization
- **includes for N+1**: Eager load associations
- **pluck for data extraction**: Skip object instantiation
- **find_each for batches**: Memory-efficient iteration
- **counter_cache**: Avoid COUNT queries
- **select specific columns**: `User.select(:id, :email)`

### Rails 8 / Hotwire
<!-- version: rails >= 7 -->
- **Turbo Streams**: Real-time updates via WebSocket
- **Turbo Frames**: Partial page updates
- **Stimulus for JS**: Small behavior controllers
- **Import maps**: No Node.js bundler required
- **Solid Cable**: Production-ready Action Cable

### API Mode
- **API-only app**: `rails new --api`
- **Serializers**: jbuilder or Blueprinter
- **Versioning**: Namespace routes and controllers
- **Token authentication**: Devise-JWT or custom

---

## Patterns to Avoid

### Model Anti-Patterns
- ❌ **Fat models**: Extract to service objects
- ❌ **Callbacks for business logic**: Explicit service calls
- ❌ **skip_validation**: Always validate
- ❌ **update_all without care**: Bypasses callbacks/validations
- ❌ **N+1 queries**: Use includes/preload

### Controller Anti-Patterns
- ❌ **Fat controllers**: Move logic to services
- ❌ **Business logic in controllers**: Controllers orchestrate
- ❌ **Before filters for data**: Use service objects
- ❌ **Rescue from everything**: Handle specific errors

### Query Anti-Patterns
- ❌ **Querying in views**: Query in controller/service
- ❌ **`.all` without pagination**: Memory issues
- ❌ **Raw SQL without bindings**: SQL injection risk
- ❌ **Missing indexes**: Index foreign keys and query fields

### Architecture Anti-Patterns
- ❌ **Concerns for non-shared code**: Keep in models
- ❌ **God services**: Split by responsibility
- ❌ **API logic in views**: Use serializers

---

## Verification Checklist

### Models
- [ ] Validations defined
- [ ] Scopes for common queries
- [ ] Indexes on foreign keys
- [ ] Associations with dependent

### Performance
- [ ] includes/preload for N+1
- [ ] Pagination on lists (Kaminari/Pagy)
- [ ] counter_cache where useful
- [ ] Database indexes verified

### Architecture
- [ ] Service objects for logic
- [ ] Serializers for JSON
- [ ] Background jobs for async (Sidekiq)
- [ ] Form objects for complex forms

### Testing
- [ ] RSpec with FactoryBot
- [ ] Request specs for controllers
- [ ] Model specs for validations
- [ ] System specs for integration

---

## Code Patterns (Reference)

### Recommended Constructs
- **Service**: `class Users::Create; def call(params); User.create!(params); end; end`
- **Scope**: `scope :active, -> { where(status: :active) }`
- **Validation**: `validates :email, presence: true, format: { with: URI::MailTo::EMAIL_REGEXP }`
- **Eager load**: `User.includes(:profile, :orders).where(status: :active)`
- **Background job**: `SendWelcomeEmailJob.perform_later(user.id)`
<!-- version: rails >= 7 -->
- **Turbo Stream**: `turbo_stream.append "users", partial: "user", locals: { user: @user }`
- **Stimulus**: `data: { controller: "toggle", action: "click->toggle#show" }`

