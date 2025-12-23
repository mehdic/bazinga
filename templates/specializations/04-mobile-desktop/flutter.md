---
name: flutter
type: framework
priority: 2
token_estimate: 600
compatible_with: [developer, senior_software_engineer]
requires: []
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Flutter Engineering Expertise

## Specialist Profile
Flutter specialist building cross-platform apps. Expert in state management, widget composition, and Dart 3 patterns.

---

## Patterns to Follow

### State Management (2025)
<!-- version: riverpod >= 2.0 -->
- **Riverpod 2+**: Compile-time safe, composable, @riverpod macro
<!-- version: flutter_bloc >= 8.0 -->
- **BLoC 8+ for enterprise**: Event → Bloc → State, strict separation
- **Mix solutions**: Riverpod for app-wide, BLoC for feature-specific
- **Flutter Signals**: Native reactive for simple local UI state
- **Local state in StatefulWidget**: Modals, form fields, ValueNotifier

### Architecture Patterns
- **Feature-first structure**: `lib/features/user/{data,domain,presentation}/`
- **Repository pattern**: Abstract data sources behind interfaces
- **Use cases/Services**: Single responsibility business logic
- **Dependency injection**: get_it or Riverpod providers
- **Clean Architecture**: Separation of concerns layers

### Widget Best Practices
- **const constructors**: `const UserCard({super.key})`
- **Widget composition**: Small, focused, reusable widgets
- **Builder pattern**: `ListView.builder`, `FutureBuilder`, `BlocBuilder`
- **Extract methods to widgets**: Not private methods returning widgets
- **Keys for stateful lists**: Preserve state during reordering

### Dart 3 Patterns
<!-- version: dart >= 3.0 -->
- **Sealed classes**: `sealed class UserState {}` for exhaustive switching
- **Pattern matching**: `switch (state) { UserLoaded(:final users) => ... }`
- **Records**: `(String name, int age)` for multiple returns
- **Class modifiers**: `final class`, `interface class`, `base class`
<!-- version: dart >= 3.3 -->
- **Extension types**: `extension type UserId(String value) implements String {}`
<!-- version: flutter >= 3.16 -->
- **Material 3 default**: New components and theming
- **Impeller rendering**: GPU-accelerated rendering on iOS

### Data Layer
- **Freezed for immutable models**: Unions, copyWith, JSON serialization
- **Dio for HTTP**: Interceptors, transformers, error handling
- **Drift or Floor for SQLite**: Type-safe local database
- **Shared preferences abstraction**: Don't use directly in UI

---

## Patterns to Avoid

### Widget Anti-Patterns
- ❌ **setState for complex state**: Use BLoC/Riverpod
- ❌ **Business logic in widgets**: Move to services/blocs
- ❌ **Missing const constructors**: Performance degradation
- ❌ **Rebuilding entire subtrees**: Use selective builders
- ❌ **Private methods returning widgets**: Extract to classes

### State Anti-Patterns
- ❌ **Provider without Riverpod for new projects**: Riverpod is successor
- ❌ **Mixing paradigms without intent**: Choose and stick
- ❌ **Global mutable state**: Use proper state management
- ❌ **Not disposing controllers**: Memory leaks

### Performance Anti-Patterns
- ❌ **Heavy computation on main thread**: Use compute()
- ❌ **Building widgets in build()**: Pre-build in initState or const
- ❌ **Unnecessary rebuilds**: Use Selector, Consumer wisely
- ❌ **Large images without caching**: Use cached_network_image

### Architecture Anti-Patterns
- ❌ **God widgets**: Split by responsibility
- ❌ **Circular dependencies**: Restructure layers
- ❌ **Domain depending on data layer**: Invert dependencies
- ❌ **Missing error handling**: Use Either or Result types

---

## Verification Checklist

### Architecture
- [ ] Feature-first folder structure
- [ ] Repository abstraction for data
- [ ] Dependency injection configured
- [ ] Clean separation of layers

### State Management
- [ ] Riverpod or BLoC configured
- [ ] Proper provider scoping
- [ ] Error states handled
- [ ] Loading states handled

### Models
- [ ] Freezed for immutable models
- [ ] Proper JSON serialization
- [ ] Sealed classes for states
- [ ] Dart 3 pattern matching

### Testing
- [ ] Widget tests with pumpWidget
- [ ] Unit tests for blocs/providers
- [ ] Integration tests
- [ ] Golden tests for visual regression

---

## Code Patterns (Reference)

### State Management
- **Riverpod provider**: `@riverpod Future<List<User>> users(Ref ref) => ref.read(userRepositoryProvider).getAll();`
- **BLoC events**: `sealed class UserEvent {}; class LoadUsers extends UserEvent {}`
- **BLoC states**: `sealed class UserState {}; class UserLoaded extends UserState { final List<User> users; }`

### Widgets
- **Stateless**: `class UserCard extends StatelessWidget { const UserCard({super.key, required this.user}); ... }`
- **BlocBuilder**: `BlocBuilder<UserBloc, UserState>(builder: (context, state) => switch (state) { ... })`
- **Consumer**: `Consumer(builder: (context, ref, child) => ...)`

### Models
- **Freezed**: `@freezed class User with _$User { const factory User({required String id, required String email}) = _User; }`
- **Sealed state**: `sealed class Result<T> {}; class Success<T> extends Result<T> { final T data; }`

### Repository
- **Interface**: `abstract interface class UserRepository { Future<List<User>> getAll(); }`
- **Implementation**: `class UserRepositoryImpl implements UserRepository { final Dio _dio; ... }`

