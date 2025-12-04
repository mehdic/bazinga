---
name: flask
type: framework
priority: 2
token_estimate: 400
compatible_with: [developer, senior_software_engineer]
requires: [python]
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Flask Engineering Expertise

## Specialist Profile
Flask specialist building lightweight APIs. Expert in Flask patterns, extensions, and application factories.

## Implementation Guidelines

### Application Factory

```python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    from app.routes import users, orders
    app.register_blueprint(users.bp)
    app.register_blueprint(orders.bp)

    return app
```

### Blueprints

```python
from flask import Blueprint, request, jsonify
from app.models import User
from app.schemas import UserSchema

bp = Blueprint('users', __name__, url_prefix='/api/users')

@bp.route('/', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify(UserSchema(many=True).dump(users))

@bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(UserSchema().dump(user))

@bp.route('/', methods=['POST'])
def create_user():
    schema = UserSchema()
    data = schema.load(request.json)
    user = User(**data)
    db.session.add(user)
    db.session.commit()
    return jsonify(schema.dump(user)), 201
```

### Error Handling

```python
from flask import jsonify
from werkzeug.exceptions import HTTPException

@app.errorhandler(HTTPException)
def handle_exception(e):
    return jsonify({
        "error": {
            "code": e.name.upper().replace(' ', '_'),
            "message": e.description,
        }
    }), e.code

@app.errorhandler(ValidationError)
def handle_validation_error(e):
    return jsonify({
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Validation failed",
            "details": e.messages,
        }
    }), 400
```

### Request Context

```python
from flask import g, current_app

def get_db():
    if 'db' not in g:
        g.db = create_connection(current_app.config['DATABASE_URL'])
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()
```

### Marshmallow Schemas

```python
from marshmallow import Schema, fields, validate, post_load

class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    email = fields.Email(required=True)
    display_name = fields.Str(required=True, validate=validate.Length(min=2))
    created_at = fields.DateTime(dump_only=True)

    @post_load
    def make_user(self, data, **kwargs):
        return User(**data)
```

## Patterns to Avoid
- ❌ Global app object (use factory)
- ❌ Business logic in routes
- ❌ Manual JSON serialization
- ❌ No request validation

## Verification Checklist
- [ ] Application factory pattern
- [ ] Blueprints for organization
- [ ] Marshmallow for serialization
- [ ] Proper error handlers
- [ ] pytest fixtures for testing
