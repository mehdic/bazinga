---
name: gin-fiber
type: framework
priority: 2
token_estimate: 400
compatible_with: [developer, senior_software_engineer]
requires: [go]
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Gin/Fiber Engineering Expertise

## Specialist Profile
Go web framework specialist building high-performance APIs. Expert in Gin, Fiber, and idiomatic Go patterns.

## Implementation Guidelines

### Gin Handlers

```go
// handlers/user.go
type UserHandler struct {
    service *UserService
}

func NewUserHandler(s *UserService) *UserHandler {
    return &UserHandler{service: s}
}

func (h *UserHandler) GetAll(c *gin.Context) {
    users, err := h.service.FindAll(c.Request.Context())
    if err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
        return
    }
    c.JSON(http.StatusOK, users)
}

func (h *UserHandler) Create(c *gin.Context) {
    var req CreateUserRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }

    user, err := h.service.Create(c.Request.Context(), req)
    if err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
        return
    }
    c.JSON(http.StatusCreated, user)
}
```

### Fiber Handlers

```go
// handlers/user.go
type UserHandler struct {
    service *UserService
}

func (h *UserHandler) GetAll(c *fiber.Ctx) error {
    users, err := h.service.FindAll(c.Context())
    if err != nil {
        return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
            "error": err.Error(),
        })
    }
    return c.JSON(users)
}

func (h *UserHandler) Create(c *fiber.Ctx) error {
    var req CreateUserRequest
    if err := c.BodyParser(&req); err != nil {
        return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
            "error": err.Error(),
        })
    }

    user, err := h.service.Create(c.Context(), req)
    if err != nil {
        return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
            "error": err.Error(),
        })
    }
    return c.Status(fiber.StatusCreated).JSON(user)
}
```

### Middleware

```go
// Gin middleware
func AuthMiddleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        token := c.GetHeader("Authorization")
        if token == "" {
            c.AbortWithStatusJSON(401, gin.H{"error": "unauthorized"})
            return
        }

        user, err := validateToken(token)
        if err != nil {
            c.AbortWithStatusJSON(401, gin.H{"error": "invalid token"})
            return
        }

        c.Set("user", user)
        c.Next()
    }
}

// Fiber middleware
func AuthMiddleware() fiber.Handler {
    return func(c *fiber.Ctx) error {
        token := c.Get("Authorization")
        if token == "" {
            return c.Status(401).JSON(fiber.Map{"error": "unauthorized"})
        }

        user, err := validateToken(token)
        if err != nil {
            return c.Status(401).JSON(fiber.Map{"error": "invalid token"})
        }

        c.Locals("user", user)
        return c.Next()
    }
}
```

### Router Setup

```go
// Gin
func SetupRouter(userHandler *UserHandler) *gin.Engine {
    r := gin.Default()
    r.Use(gin.Recovery())

    api := r.Group("/api/v1")
    {
        users := api.Group("/users")
        users.GET("", userHandler.GetAll)
        users.POST("", userHandler.Create)
        users.GET("/:id", userHandler.GetByID)
    }

    return r
}

// Fiber
func SetupRouter(userHandler *UserHandler) *fiber.App {
    app := fiber.New(fiber.Config{
        ErrorHandler: customErrorHandler,
    })

    api := app.Group("/api/v1")
    users := api.Group("/users")
    users.Get("/", userHandler.GetAll)
    users.Post("/", userHandler.Create)

    return app
}
```

## Patterns to Avoid
- ❌ Panic in handlers (return errors)
- ❌ Global state
- ❌ Blocking operations without context
- ❌ Missing graceful shutdown

## Verification Checklist
- [ ] Proper error handling
- [ ] Context propagation
- [ ] Middleware for cross-cutting
- [ ] Graceful shutdown
- [ ] Request validation
