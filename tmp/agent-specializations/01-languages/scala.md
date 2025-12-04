---
name: scala
type: language
priority: 1
token_estimate: 400
compatible_with: [developer, senior_software_engineer]
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Scala Engineering Expertise

## Specialist Profile
Scala specialist blending functional and object-oriented paradigms. Expert in type safety, immutability, and Cats/ZIO.

## Implementation Guidelines

### Case Classes

```scala
case class User(
  id: UUID,
  email: String,
  displayName: String,
  createdAt: Instant = Instant.now()
)

case class CreateUserRequest(email: String, displayName: String)
```

### Option Handling

```scala
def findUser(id: UUID): Option[User] =
  repository.find(id)

def getDisplayName(user: Option[User]): String =
  user.map(_.displayName).getOrElse("Unknown")

// Pattern matching
user match {
  case Some(u) => processUser(u)
  case None => handleMissing()
}

// For comprehension
for {
  user <- findUser(id)
  profile <- user.profile
} yield profile.displayName
```

### Either for Errors

```scala
sealed trait UserError
case class NotFound(id: UUID) extends UserError
case class InvalidEmail(email: String) extends UserError

def createUser(request: CreateUserRequest): Either[UserError, User] =
  for {
    _ <- validateEmail(request.email)
    user <- Right(User(UUID.randomUUID(), request.email, request.displayName))
  } yield user
```

### Pattern Matching

```scala
def processEvent(event: Event): String = event match {
  case UserCreated(id, email) => s"User $id created with $email"
  case UserDeleted(id) => s"User $id deleted"
  case _ => "Unknown event"
}
```

### Implicits/Givens

<!-- version: scala >= 3 -->
```scala
given Ordering[User] = Ordering.by(_.createdAt)

extension (s: String)
  def toSlug: String = s.toLowerCase.replaceAll("[^a-z0-9]+", "-")
```

## Patterns to Avoid
- ❌ null (use Option)
- ❌ Mutable collections
- ❌ Exceptions for control flow
- ❌ Overusing implicits

## Verification Checklist
- [ ] Immutable data structures
- [ ] Option instead of null
- [ ] Either for error handling
- [ ] Pattern matching exhaustive
- [ ] Pure functions where possible
