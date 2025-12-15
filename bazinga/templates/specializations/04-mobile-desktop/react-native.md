---
name: react-native
type: framework
priority: 2
token_estimate: 600
compatible_with: [developer, senior_software_engineer]
requires: [typescript, javascript]
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# React Native Engineering Expertise

## Specialist Profile
React Native specialist building cross-platform mobile apps. Expert in New Architecture, Expo, and performance optimization.

---

## Patterns to Follow

### New Architecture (RN 0.82+)
<!-- version: react-native >= 0.82 -->
- **Fabric Renderer**: Smoother animations, better native interop
- **TurboModules**: Faster startup, efficient JS-native communication
- **Hermes Engine**: Reduced memory, faster startup times
- **Bridgeless mode**: Direct native calls without bridge overhead

### Component Patterns
- **Functional components with hooks**: Prefer over class components
- **React.memo for expensive components**: Prevent unnecessary re-renders
- **Custom hooks for reusable logic**: `useUsers`, `useAuth`, `useForm`
- **Feature-based folder structure**: Group by feature not file type
- **Atomic design**: Atoms → Molecules → Organisms → Templates

### State Management
- **React Query/TanStack Query**: Server state management
- **Zustand or Jotai**: Simple client state
- **Context for low-frequency updates**: Theme, locale
- **Local state for UI-only**: Form inputs, toggles

### List Optimization
- **FlatList with keyExtractor**: Never use index as key
- **removeClippedSubviews**: Unmount off-screen items
- **maxToRenderPerBatch**: Control batch size (default 10)
- **windowSize**: Render window (default 21)
- **getItemLayout for fixed heights**: Skip measurement

### Navigation
- **React Navigation v6+**: Type-safe with TypeScript
- **Native Stack Navigator**: Native performance
- **Deep linking configuration**: Universal links support
- **Expo Router**: File-based routing for Expo projects

### Expo Best Practices
- **Expo SDK 53+**: New Architecture support
- **EAS Build**: Cloud builds with native modules
- **Expo Router**: Next.js-like file routing
- **Config plugins**: Extend native configuration

---

## Patterns to Avoid

### Performance Anti-Patterns
- ❌ **Anonymous functions in renderItem**: Creates new function each render
- ❌ **Inline styles everywhere**: Use StyleSheet for optimization
- ❌ **Missing keyExtractor**: Causes list re-render issues
- ❌ **Large images without resizing**: Memory bloat
- ❌ **Synchronous storage operations**: Block JS thread

### Component Anti-Patterns
- ❌ **Business logic in components**: Use hooks/services
- ❌ **Prop drilling deeply**: Use context or state library
- ❌ **Missing memo for expensive renders**: Profile with Flipper
- ❌ **Using index as key in lists**: Breaks reconciliation

### Navigation Anti-Patterns
- ❌ **Untyped navigation params**: Type with RootStackParamList
- ❌ **Heavy computation during navigation**: Defer with InteractionManager
- ❌ **Missing back handler on Android**: Handle hardware back button
- ❌ **Nested navigators without care**: Complex state management

### State Anti-Patterns
- ❌ **Storing derived state**: Compute from source
- ❌ **Global state for local concerns**: Keep UI state local
- ❌ **Missing error boundaries**: App crashes on error
- ❌ **Not handling loading states**: Poor UX

---

## Verification Checklist

### Architecture
- [ ] New Architecture enabled (SDK 53+)
- [ ] Feature-based folder structure
- [ ] TypeScript throughout
- [ ] Custom hooks for shared logic

### Performance
- [ ] FlatList optimized (keyExtractor, getItemLayout)
- [ ] React.memo on expensive components
- [ ] Images optimized and cached
- [ ] Hermes engine enabled

### Navigation
- [ ] Type-safe navigation params
- [ ] Deep linking configured
- [ ] Android back handler
- [ ] Screen options optimized

### Testing
- [ ] Jest for unit tests
- [ ] React Native Testing Library for components
- [ ] Detox for E2E (native) or Maestro
- [ ] Test on both platforms

---

## Code Patterns (Reference)

### Components
- **Screen**: `export function UserListScreen() { const { data, isLoading } = useUsers(); ... }`
- **FlatList**: `<FlatList data={users} keyExtractor={u => u.id} renderItem={UserCard} getItemLayout={...} />`
- **Memoized**: `export const UserCard = React.memo(({ user }: Props) => ...)`

### Hooks
- **Query hook**: `export function useUsers() { return useQuery({ queryKey: ['users'], queryFn: api.getUsers }); }`
- **Mutation hook**: `export function useCreateUser() { return useMutation({ mutationFn: api.createUser, onSuccess: ... }); }`

### Navigation
- **Type-safe params**: `export type RootStackParamList = { Home: undefined; User: { id: string } };`
- **Navigator**: `const Stack = createNativeStackNavigator<RootStackParamList>();`

### Platform-Specific
- **Platform.select**: `Platform.select({ ios: styles.iosShadow, android: styles.elevation })`
- **File extension**: `Button.ios.tsx`, `Button.android.tsx`

