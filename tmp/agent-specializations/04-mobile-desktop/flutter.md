---
name: flutter
type: framework
priority: 2
token_estimate: 450
compatible_with: [developer, senior_software_engineer]
requires: []
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Flutter Engineering Expertise

## Specialist Profile
Flutter specialist building cross-platform apps. Expert in widgets, state management, and Dart patterns.

## Implementation Guidelines

### Screens

```dart
// lib/screens/user_list_screen.dart
class UserListScreen extends StatelessWidget {
  const UserListScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Users')),
      body: BlocBuilder<UserBloc, UserState>(
        builder: (context, state) {
          return switch (state) {
            UserLoading() => const Center(child: CircularProgressIndicator()),
            UserError(:final message) => Center(child: Text(message)),
            UserLoaded(:final users) => ListView.separated(
              itemCount: users.length,
              separatorBuilder: (_, __) => const SizedBox(height: 8),
              itemBuilder: (context, index) => UserCard(user: users[index]),
            ),
          };
        },
      ),
    );
  }
}
```

### BLoC Pattern

```dart
// lib/bloc/user_bloc.dart
sealed class UserEvent {}
class LoadUsers extends UserEvent {}
class CreateUser extends UserEvent {
  final CreateUserRequest request;
  CreateUser(this.request);
}

sealed class UserState {}
class UserInitial extends UserState {}
class UserLoading extends UserState {}
class UserLoaded extends UserState {
  final List<User> users;
  UserLoaded(this.users);
}
class UserError extends UserState {
  final String message;
  UserError(this.message);
}

class UserBloc extends Bloc<UserEvent, UserState> {
  final UserRepository _repository;

  UserBloc(this._repository) : super(UserInitial()) {
    on<LoadUsers>(_onLoadUsers);
    on<CreateUser>(_onCreateUser);
  }

  Future<void> _onLoadUsers(LoadUsers event, Emitter<UserState> emit) async {
    emit(UserLoading());
    try {
      final users = await _repository.getAll();
      emit(UserLoaded(users));
    } catch (e) {
      emit(UserError(e.toString()));
    }
  }
}
```

### Repository Pattern

```dart
// lib/repositories/user_repository.dart
abstract interface class UserRepository {
  Future<List<User>> getAll();
  Future<User> getById(String id);
  Future<User> create(CreateUserRequest request);
}

class UserRepositoryImpl implements UserRepository {
  final ApiClient _client;
  UserRepositoryImpl(this._client);

  @override
  Future<List<User>> getAll() async {
    final response = await _client.get('/users');
    return (response.data as List).map((e) => User.fromJson(e)).toList();
  }
}
```

### Models with Freezed

```dart
// lib/models/user.dart
@freezed
class User with _$User {
  const factory User({
    required String id,
    required String email,
    required String displayName,
    @Default(UserStatus.active) UserStatus status,
  }) = _User;

  factory User.fromJson(Map<String, dynamic> json) => _$UserFromJson(json);
}
```

## Patterns to Avoid
- ❌ setState for complex state
- ❌ Business logic in widgets
- ❌ Missing const constructors
- ❌ Blocking the UI thread

## Verification Checklist
- [ ] BLoC or Riverpod for state
- [ ] Freezed for models
- [ ] Repository abstraction
- [ ] Dart 3 patterns (switch expressions)
- [ ] Widget tests
