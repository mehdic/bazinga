---
name: spring-boot
type: framework
priority: 2
token_estimate: 650
compatible_with: [developer, senior_software_engineer]
requires: [java]
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Spring Boot Engineering Expertise

## Specialist Profile
Spring Boot specialist building production-grade applications. Expert in dependency injection, JPA, and reactive patterns.

---

## Patterns to Follow

### Layered Architecture
- **Controller → Service → Repository**: Clear separation
- **DTOs for APIs**: Don't expose entities
- **Mappers**: MapStruct or manual for entity ↔ DTO
- **Thin controllers**: Validation and routing only
- **Fat services**: Business logic here

### Dependency Injection
- **Constructor injection**: Immutable dependencies
- **`@RequiredArgsConstructor`**: Lombok for brevity
<!-- version: spring-boot >= 3.0 -->
- **`@Autowired` optional**: Single constructor auto-wired by default
<!-- version: spring-boot < 3.0 -->
- **`@Autowired` explicit**: Add on constructor for clarity
<!-- version: spring-boot >= 2.2 -->
- **`@ConfigurationProperties`**: Type-safe config with records (3.0+) or POJOs
- **Interface-based design**: For testability
- **`@Qualifier` for ambiguity**: Multiple implementations

### Transaction Management
- **`@Transactional` on services**: Not controllers
- **`readOnly = true` for reads**: Optimization hint
- **Propagation understanding**: REQUIRED vs REQUIRES_NEW
- **Rollback for checked**: Configure explicitly

### Virtual Threads (Spring Boot 3.2+)
<!-- version: spring-boot >= 3.2 -->
- **Enable via property**: `spring.threads.virtual.enabled=true`
- **2x throughput improvement**: For blocking I/O
- **No code changes needed**: Automatic executor
- **Not for CPU-bound**: Only benefits I/O

### Data Access
- **JPA repositories**: Spring Data magic
- **`@EntityGraph`**: Solve N+1 selectively
- **Native queries sparingly**: When JPA isn't enough
- **Pagination**: `Pageable` parameter

---

## Patterns to Avoid

### DI Anti-Patterns
- ❌ **Field injection**: Use constructor
- ❌ **Circular dependencies**: Restructure
- ❌ **`new` for services**: Let Spring manage
- ❌ **Static methods on services**: Inject instances

### Transaction Anti-Patterns
- ❌ **`@Transactional` on controllers**: Service layer only
- ❌ **Missing `readOnly`**: Performance impact
- ❌ **Long transactions**: Hold locks briefly
- ❌ **Catching exceptions inside**: Breaks rollback

### JPA Anti-Patterns
- ❌ **N+1 queries**: Use `@EntityGraph` or fetch join
- ❌ **Exposing entities**: Use DTOs
- ❌ **Lazy loading in controllers**: Initialize in service
- ❌ **`findAll()` without pagination**: Memory issues

### Performance Anti-Patterns
- ❌ **Fixed thread pool with virtual threads**: Use virtual executor
- ❌ **Blocking in reactive**: Choose one paradigm
- ❌ **No caching**: Use `@Cacheable` where appropriate
- ❌ **Missing indexes**: Check query plans

---

## Verification Checklist

### Architecture
- [ ] Constructor injection everywhere
- [ ] DTOs for API boundaries
- [ ] Services for business logic
- [ ] Global exception handling

### Transactions
- [ ] `@Transactional` on service methods
- [ ] `readOnly = true` for queries
- [ ] Proper rollback configuration
- [ ] No long-running transactions

### Performance
- [ ] N+1 queries addressed
- [ ] Pagination on lists
- [ ] Caching strategy defined
- [ ] Indexes verified

### Testing
- [ ] `@WebMvcTest` for controllers
- [ ] `@SpringBootTest` for integration
- [ ] `@MockBean` for dependencies
- [ ] `@Transactional` for test rollback

---

## Code Patterns (Reference)

### Recommended Constructs
- **Controller**: `@RestController @RequestMapping("/api/users") class UserController {}`
- **Service**: `@Service @Transactional(readOnly = true) class UserService {}`
- **Repository**: `interface UserRepository extends JpaRepository<User, UUID> {}`
<!-- version: spring-boot >= 3.0 -->
- **DTO**: `record CreateUserRequest(@jakarta.validation.constraints.NotBlank @jakarta.validation.constraints.Email String email) {}`
- **Config**: `@ConfigurationProperties(prefix = "app") record AppConfig(String apiKey, Duration timeout) {}`
<!-- version: spring-boot < 3.0 -->
- **DTO**: Class with `@javax.validation.constraints.NotBlank` annotations
- **Config**: POJO class with `@ConfigurationProperties` (records require 3.0+)
<!-- version: spring-boot >= 2.0 -->
- **Exception**: `@ExceptionHandler(NotFoundException.class) ResponseEntity<?> handle(e) {...}`
<!-- version: spring-boot >= 3.2 -->
- **Virtual threads**: `spring.threads.virtual.enabled=true` (properties)

