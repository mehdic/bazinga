---
name: flask
type: framework
priority: 2
token_estimate: 500
compatible_with: [developer, senior_software_engineer]
requires: [python]
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Flask Engineering Expertise

## Specialist Profile
Flask specialist building lightweight APIs. Expert in application factories, blueprints, and Flask extensions.

---

## Patterns to Follow

### Application Factory
- **create_app() pattern**: Factory for app instances
- **Config classes**: Per-environment configuration
- **Extension initialization**: `ext.init_app(app)` pattern
- **Blueprint registration**: Modular route organization
- **Error handler registration**: Consistent error responses

### Blueprints
- **Feature-based organization**: One blueprint per domain
- **URL prefixes**: `/api/users`, `/api/orders`
- **Nested blueprints**: For API versioning
- **Blueprint-local error handlers**: Domain-specific errors

### Request/Response
- **Marshmallow for validation**: Schema-based serialization
- **Flask-SQLAlchemy**: ORM integration
- **Request context**: `g` for request-scoped data
- **Proper status codes**: 201 for create, 204 for delete
<!-- version: flask >= 2.0 -->
- **Async views**: `async def` routes with ASGI
- **Nested blueprints**: `bp.register_blueprint(child_bp)`
- **Shorthand decorators**: `@app.get()`, `@app.post()` instead of `@app.route(methods=[...])`
<!-- version: flask >= 3.0 -->
- **Python 3.8+ required**: No more Python 3.7 support
- **Removed @before_first_request**: Use app context setup instead

### Error Handling
- **Global error handlers**: `@app.errorhandler`
- **Custom exception classes**: Domain-specific errors
- **Structured error responses**: Consistent JSON format
- **Logging**: Log errors before responding

### Extensions
- **Flask-SQLAlchemy**: Database ORM
- **Flask-Migrate**: Alembic migrations
- **Flask-JWT-Extended**: JWT authentication
- **Flask-CORS**: Cross-origin support

---

## Patterns to Avoid

### Application Anti-Patterns
- ❌ **Global app object**: Use application factory
- ❌ **Import-time configuration**: Configure in factory
- ❌ **Circular imports**: Use blueprints properly
- ❌ **Hardcoded secrets**: Use environment variables

### Route Anti-Patterns
- ❌ **Business logic in routes**: Use services
- ❌ **Manual JSON serialization**: Use Marshmallow
- ❌ **No request validation**: Always validate input
- ❌ **Missing error handlers**: Handle all exceptions

### Database Anti-Patterns
- ❌ **Session leaks**: Use `teardown_appcontext`
- ❌ **N+1 queries**: Use joinedload/subqueryload
- ❌ **Raw SQL without params**: Use parameterized queries
- ❌ **No connection pooling**: SQLAlchemy handles it

### Testing Anti-Patterns
- ❌ **Testing production DB**: Use test database
- ❌ **No fixtures**: Use pytest fixtures
- ❌ **Shared state between tests**: Isolate tests
- ❌ **Testing implementation details**: Test behavior

---

## Verification Checklist

### Application Structure
- [ ] Application factory pattern
- [ ] Config classes per environment
- [ ] Blueprints for organization
- [ ] Extensions initialized properly

### Validation & Serialization
- [ ] Marshmallow schemas defined
- [ ] Request validation on all inputs
- [ ] Consistent response formats
- [ ] Proper HTTP status codes

### Error Handling
- [ ] Global exception handlers
- [ ] Structured error responses
- [ ] Logging configured
- [ ] 404/500 handlers defined

### Testing
- [ ] pytest with fixtures
- [ ] Test client usage
- [ ] Database isolation
- [ ] Factory for test app

---

## Code Patterns (Reference)

### Recommended Constructs
- **Factory**: `def create_app(config=Config): app = Flask(__name__); db.init_app(app); return app`
- **Blueprint**: `bp = Blueprint('users', __name__, url_prefix='/api/users')`
- **Route**: `@bp.route('/', methods=['POST']) def create(): ...`
- **Schema**: `class UserSchema(Schema): email = fields.Email(required=True)`
- **Error handler**: `@app.errorhandler(HTTPException) def handle(e): return jsonify(error=e.description), e.code`
- **Context**: `@app.teardown_appcontext def shutdown(exception): db.session.remove()`

