---
name: nestjs
type: framework
priority: 2
token_estimate: 600
compatible_with: [developer, senior_software_engineer]
requires: [typescript]
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# NestJS Engineering Expertise

## Specialist Profile
NestJS specialist building enterprise Node.js applications. Expert in decorators, dependency injection, and modular architecture.

---

## Patterns to Follow

### Module Organization
- **Feature modules**: One module per domain (UsersModule, OrdersModule)
- **Shared modules**: Common utilities, pipes, interceptors
- **Single responsibility**: Clear module boundaries
- **Lazy loading**: For large applications
- **Re-export pattern**: `exports: [UsersService]` for module APIs
<!-- version: nestjs >= 8.0 -->
- **Standalone applications**: `NestFactory.createApplicationContext()`
<!-- version: nestjs >= 9.0 -->
- **REPL support**: Interactive shell for debugging
- **ConfigModule improvements**: Better env validation
<!-- version: nestjs >= 10.0 -->
- **Node 18+ required**: Minimum Node.js version
- **Fastify v4 support**: Updated adapter

### Dependency Injection
- **Constructor injection**: Let NestJS resolve dependencies
- **Custom providers**: useFactory, useValue, useClass
- **Scope management**: Default singleton, request scope when needed
- **Interface + token pattern**: For abstraction
- **Avoid circular deps**: Restructure or use forwardRef

### Controllers & Services
- **Thin controllers**: Orchestration only
- **Fat services**: Business logic here
- **DTOs for validation**: class-validator decorators
- **Response transformation**: class-transformer or custom
- **Guards for authorization**: Reusable auth logic

### Exception Handling
- **Exception filters**: `@Catch()` decorator
- **Built-in exceptions**: HttpException hierarchy
- **Custom exceptions**: Domain-specific errors
- **Global vs local filters**: Scope appropriately

### Swagger/OpenAPI
- **Decorators for docs**: `@ApiOperation`, `@ApiResponse`
- **DTO decorators**: `@ApiProperty` for schema
- **Tags for grouping**: Organize endpoints
- **Examples**: Provide request/response examples

---

## Patterns to Avoid

### Module Anti-Patterns
- ❌ **God modules**: Split by domain
- ❌ **SharedModule abuse**: Only truly shared code
- ❌ **Circular module deps**: Restructure
- ❌ **Skipping modules**: Every feature needs one

### DI Anti-Patterns
- ❌ **Manual instantiation**: Use NestJS DI
- ❌ **Static methods for services**: Inject instances
- ❌ **Circular dependencies**: forwardRef as last resort
- ❌ **Request scope everywhere**: Performance impact

### Controller Anti-Patterns
- ❌ **Business logic in controllers**: Use services
- ❌ **No validation decorators**: Always validate DTOs
- ❌ **Missing guards**: Explicit authorization
- ❌ **Bypassing DTOs**: Validate all input

### Architecture Anti-Patterns
- ❌ **Express patterns directly**: Use Nest's structure
- ❌ **No exception filters**: Handle errors consistently
- ❌ **Missing Swagger decorators**: Document APIs
- ❌ **Hardcoded config**: Use ConfigModule

---

## Verification Checklist

### Architecture
- [ ] Feature-based modules
- [ ] Thin controllers, fat services
- [ ] DTOs with class-validator
- [ ] Exception filters configured

### DI
- [ ] Constructor injection
- [ ] No circular dependencies
- [ ] Proper scoping
- [ ] Custom providers where needed

### Security
- [ ] Guards for authorization
- [ ] Rate limiting (ThrottlerModule)
- [ ] Validation pipes globally
- [ ] Helmet middleware

### Documentation
- [ ] Swagger decorators on controllers
- [ ] API property decorators on DTOs
- [ ] Response type decorators
- [ ] Examples provided

---

## Code Patterns (Reference)

### Recommended Constructs
- **Module**: `@Module({ imports: [], controllers: [], providers: [], exports: [] })`
- **Controller**: `@Controller('users') class UsersController { constructor(private usersService: UsersService) {} }`
- **Service**: `@Injectable() class UsersService { constructor(@InjectRepository(User) private repo: Repository<User>) {} }`
- **DTO**: `class CreateUserDto { @IsEmail() email: string; @MinLength(2) displayName: string; }`
- **Guard**: `@UseGuards(JwtAuthGuard) @Get('profile')`
- **Filter**: `@Catch(HttpException) class HttpExceptionFilter implements ExceptionFilter { catch(e, host) {...} }`
- **Pipe**: `@UsePipes(new ValidationPipe({ transform: true }))`

