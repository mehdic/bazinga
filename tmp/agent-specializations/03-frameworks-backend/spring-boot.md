---
name: spring-boot
type: framework
priority: 2
token_estimate: 600
compatible_with: [developer, senior_software_engineer]
requires: [java]
---

> **PRECEDENCE**: Base agent workflow, routing, and reporting rules take precedence over this guidance.

# Spring Boot Engineering Expertise

## Specialist Profile

Spring Boot specialist building production-grade applications. Deep understanding of Spring ecosystem, dependency injection, and reactive patterns.

## Implementation Guidelines

### Controller Layer

<!-- version: spring-boot >= 3.0 -->
```java
@RestController
@RequestMapping("/api/v1/users")
@RequiredArgsConstructor
@Tag(name = "Users", description = "User management endpoints")
public class UserController {

    private final UserService userService;

    @GetMapping("/{id}")
    @Operation(summary = "Get user by ID")
    public ResponseEntity<UserDto> getUser(@PathVariable UUID id) {
        return userService.findById(id)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public UserDto createUser(@Valid @RequestBody CreateUserRequest request) {
        return userService.create(request);
    }
}
```

<!-- version: spring-boot >= 2.0, spring-boot < 3.0 -->
```java
@RestController
@RequestMapping("/api/v1/users")
@RequiredArgsConstructor
@Api(tags = "Users")
public class UserController {

    private final UserService userService;

    @GetMapping("/{id}")
    @ApiOperation("Get user by ID")
    public ResponseEntity<UserDto> getUser(@PathVariable UUID id) {
        return userService.findById(id)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public UserDto createUser(@Valid @RequestBody CreateUserRequest request) {
        return userService.create(request);
    }
}
```

### Service Layer

```java
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class UserService {

    private final UserRepository userRepository;
    private final UserMapper userMapper;

    public Optional<UserDto> findById(UUID id) {
        return userRepository.findById(id)
            .map(userMapper::toDto);
    }

    @Transactional
    public UserDto create(CreateUserRequest request) {
        User user = userMapper.toEntity(request);
        User saved = userRepository.save(user);
        return userMapper.toDto(saved);
    }

    public Page<UserDto> findAll(Pageable pageable) {
        return userRepository.findAll(pageable)
            .map(userMapper::toDto);
    }
}
```

### Repository Layer

```java
public interface UserRepository extends JpaRepository<User, UUID> {

    Optional<User> findByEmail(String email);

    @Query("SELECT u FROM User u WHERE u.status = :status")
    Page<User> findByStatus(@Param("status") UserStatus status, Pageable pageable);

    boolean existsByEmail(String email);
}
```

### Exception Handling

```java
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(EntityNotFoundException.class)
    public ResponseEntity<ErrorResponse> handleNotFound(EntityNotFoundException ex) {
        return ResponseEntity.status(HttpStatus.NOT_FOUND)
            .body(new ErrorResponse("NOT_FOUND", ex.getMessage()));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleValidation(MethodArgumentNotValidException ex) {
        List<FieldError> errors = ex.getBindingResult().getFieldErrors().stream()
            .map(e -> new FieldError(e.getField(), e.getDefaultMessage()))
            .toList();
        return ResponseEntity.badRequest()
            .body(new ErrorResponse("VALIDATION_ERROR", "Validation failed", errors));
    }
}
```

### Configuration

<!-- style: uses_lombok -->
```java
@Configuration
@ConfigurationProperties(prefix = "app")
@Data
public class AppProperties {
    private String apiKey;
    private Duration timeout = Duration.ofSeconds(30);
    private int maxRetries = 3;
}
```

<!-- style: !uses_lombok -->
```java
@Configuration
@ConfigurationProperties(prefix = "app")
public class AppProperties {
    private String apiKey;
    private Duration timeout = Duration.ofSeconds(30);
    private int maxRetries = 3;

    // Getters and setters...
}
```

### Testing

```java
@WebMvcTest(UserController.class)
class UserControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private UserService userService;

    @Test
    void getUser_whenExists_returnsUser() throws Exception {
        UUID id = UUID.randomUUID();
        UserDto user = new UserDto(id, "test@example.com", "Test User");
        when(userService.findById(id)).thenReturn(Optional.of(user));

        mockMvc.perform(get("/api/v1/users/{id}", id))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.email").value("test@example.com"));
    }

    @Test
    void getUser_whenNotExists_returns404() throws Exception {
        UUID id = UUID.randomUUID();
        when(userService.findById(id)).thenReturn(Optional.empty());

        mockMvc.perform(get("/api/v1/users/{id}", id))
            .andExpect(status().isNotFound());
    }
}

@SpringBootTest
@Transactional
class UserServiceIntegrationTest {

    @Autowired
    private UserService userService;

    @Test
    void create_savesUser() {
        CreateUserRequest request = new CreateUserRequest("test@example.com", "Test");
        UserDto result = userService.create(request);

        assertThat(result.email()).isEqualTo("test@example.com");
        assertThat(userService.findById(result.id())).isPresent();
    }
}
```

## Patterns to Avoid

- Field injection (`@Autowired` on fields) → Use constructor injection
- Business logic in controllers → Move to service layer
- Missing `@Transactional` on write operations
- N+1 queries → Use `@EntityGraph` or join fetch
- Exposing entities directly → Use DTOs
- Hardcoded configuration → Use `@ConfigurationProperties`

## Verification Checklist

- [ ] Constructor injection for all dependencies
- [ ] `@Transactional` on service methods (readOnly=true for reads)
- [ ] Proper HTTP status codes (201 for create, 204 for delete)
- [ ] Request validation with `@Valid`
- [ ] Global exception handling
- [ ] Unit tests for controllers with MockMvc
- [ ] Integration tests with @SpringBootTest
