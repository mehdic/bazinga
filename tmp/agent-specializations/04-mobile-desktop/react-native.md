---
name: react-native
type: framework
priority: 2
token_estimate: 450
compatible_with: [developer, senior_software_engineer]
requires: [typescript]
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# React Native Engineering Expertise

## Specialist Profile
React Native specialist building cross-platform mobile apps. Expert in native modules, navigation, and performance optimization.

## Implementation Guidelines

### Screens

```tsx
// screens/UserListScreen.tsx
import { FlatList, StyleSheet, View } from 'react-native';
import { useUsers } from '../hooks/useUsers';
import { UserCard } from '../components/UserCard';
import { LoadingSpinner } from '../components/LoadingSpinner';

export function UserListScreen() {
  const { data: users, isLoading, refetch } = useUsers();

  if (isLoading) return <LoadingSpinner />;

  return (
    <View style={styles.container}>
      <FlatList
        data={users}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => <UserCard user={item} />}
        onRefresh={refetch}
        refreshing={isLoading}
        ItemSeparatorComponent={() => <View style={styles.separator} />}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
  separator: { height: 8 },
});
```

### Navigation

```tsx
// navigation/RootNavigator.tsx
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';

export type RootStackParamList = {
  Home: undefined;
  UserDetails: { userId: string };
  Settings: undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();

export function RootNavigator() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="Home" component={HomeScreen} />
      <Stack.Screen name="UserDetails" component={UserDetailsScreen} />
    </Stack.Navigator>
  );
}
```

### Custom Hooks

```tsx
// hooks/useUsers.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';

export function useUsers() {
  return useQuery({
    queryKey: ['users'],
    queryFn: api.getUsers,
  });
}

export function useCreateUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.createUser,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['users'] }),
  });
}
```

### Platform-Specific Code

```tsx
// components/Button.tsx
import { Platform, Pressable, StyleSheet, Text } from 'react-native';

export function Button({ title, onPress }: ButtonProps) {
  return (
    <Pressable
      style={({ pressed }) => [
        styles.button,
        Platform.select({
          ios: pressed && styles.pressedIos,
          android: {},  // Uses built-in ripple
        }),
      ]}
      android_ripple={{ color: 'rgba(0,0,0,0.1)' }}
      onPress={onPress}
    >
      <Text style={styles.text}>{title}</Text>
    </Pressable>
  );
}
```

## Patterns to Avoid
- ❌ Inline styles everywhere (use StyleSheet)
- ❌ Anonymous functions in renderItem
- ❌ Missing keyExtractor in lists
- ❌ Synchronous storage operations

## Verification Checklist
- [ ] TypeScript navigation types
- [ ] React Query for data fetching
- [ ] FlatList for long lists
- [ ] Platform-specific handling
- [ ] Proper list optimization
