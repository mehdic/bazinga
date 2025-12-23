---
name: electron-tauri
type: framework
priority: 2
token_estimate: 600
compatible_with: [developer, senior_software_engineer]
requires: [typescript]
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Electron/Tauri Desktop Expertise

## Specialist Profile
Desktop app specialist building cross-platform apps. Expert in IPC security, native APIs, and performance optimization.

---

## Patterns to Follow

### Tauri 2.0 (2025 Recommended)
<!-- version: tauri >= 2.0 -->
- **Rust backend**: Memory-safe, high performance
- **OS native webview**: WebView2 (Windows), WebKit (macOS/Linux)
- **Deny by default security**: Explicit permission grants
- **3MB binary size**: vs 200MB+ Electron
- **30MB RAM usage**: vs 250MB+ Electron idle
- **Mobile support**: iOS and Android in v2.0
- **Capabilities system**: Fine-grained permission model
<!-- version: tauri >= 1.0, tauri < 2.0 -->
- **Allowlist pattern**: Coarser permission model (deprecated in v2)
- **No mobile support**: Desktop only

### Tauri Patterns
- **Commands for IPC**: `#[tauri::command]` decorated functions
- **State management**: `State<'_, T>` injection
- **Error handling**: Return `Result<T, String>` from commands
- **Event system**: Frontend ↔ Backend communication
- **Plugin system**: Extend functionality modularly

### Electron Security
- **contextIsolation: true**: Always enable
- **nodeIntegration: false**: Never enable in renderer
- **Preload scripts**: Expose limited API via contextBridge
- **sandbox: true**: Sandbox renderer processes
- **CSP headers**: Prevent XSS attacks

### Electron Patterns
- **IPC handlers**: `ipcMain.handle` for async, `ipcMain.on` for events
- **Preload bridge**: `contextBridge.exposeInMainWorld`
- **Window management**: BrowserWindow with proper options
- **Auto-updates**: electron-updater integration
<!-- version: electron >= 28 -->
- **ESM support**: Native ES modules in main process
- **V8 sandbox by default**: Enhanced security
<!-- version: electron >= 30 -->
- **Improved utilityProcess**: Better child process handling

### Cross-Platform
- **App icons**: Platform-specific formats
- **Menu bar**: Native menus where applicable
- **File associations**: Register file types
- **Native dialogs**: Open, save, message boxes

---

## Patterns to Avoid

### Security Anti-Patterns (Critical)
- ❌ **nodeIntegration: true**: Full Node.js in renderer = RCE
- ❌ **contextIsolation: false**: Prototype pollution attacks
- ❌ **Exposing require() to renderer**: Code injection
- ❌ **Disabling webSecurity**: CORS protection lost
- ❌ **Remote module usage**: Deprecated, insecure

### Tauri Anti-Patterns
- ❌ **Overly permissive allowlist**: Minimal permissions
- ❌ **Sync commands blocking UI**: Use async
- ❌ **Missing error handling in Rust**: Return Result types
- ❌ **Direct filesystem access without scope**: Use path scope

### Electron Anti-Patterns
- ❌ **Synchronous IPC (sendSync)**: Blocks renderer
- ❌ **Multiple BrowserWindow instances needlessly**: RAM bloat
- ❌ **Loading remote URLs without verification**: Security risk
- ❌ **Missing ASAR packaging**: File tampering

### Performance Anti-Patterns
- ❌ **Heavy computation in main process**: Blocks all windows
- ❌ **Large IPC payloads**: Serialize efficiently
- ❌ **Memory leaks from event listeners**: Remove on cleanup
- ❌ **Bundling entire node_modules**: Tree-shake dependencies

---

## Verification Checklist

### Security (Critical)
- [ ] contextIsolation enabled
- [ ] nodeIntegration disabled
- [ ] Preload script with minimal API
- [ ] CSP headers configured
- [ ] Input validation on IPC

### Tauri-Specific
- [ ] Minimal capability permissions
- [ ] Path scoping configured
- [ ] Async commands for blocking ops
- [ ] Error types properly returned

### Electron-Specific
- [ ] sandbox enabled
- [ ] Remote module not used
- [ ] Auto-updater configured
- [ ] ASAR packaging enabled

### Cross-Platform
- [ ] Tested on all target platforms
- [ ] Native menus configured
- [ ] App icons for each platform
- [ ] Installer/DMG/AppImage created

---

## Code Patterns (Reference)

### Tauri Commands
- **Async command**: `#[tauri::command] async fn get_users(db: State<'_, Database>) -> Result<Vec<User>, String> { ... }`
- **Invoke**: `await invoke<User[]>('get_users')`
- **With args**: `invoke('create_user', { request })`
- **Error handling**: `.map_err(|e| e.to_string())`

### Electron Main
- **Window**: `new BrowserWindow({ webPreferences: { contextIsolation: true, nodeIntegration: false, preload: '...' } })`
- **Handler**: `ipcMain.handle('get-users', async () => db.getUsers())`

### Electron Preload
- **Bridge**: `contextBridge.exposeInMainWorld('api', { getUsers: () => ipcRenderer.invoke('get-users') })`
- **Typed**: `declare global { interface Window { api: { getUsers: () => Promise<User[]> } } }`

### Tauri Config (tauri.conf.json)
- **Capabilities**: `"permissions": ["path:default", "fs:read-files"]`
- **Window**: `"windows": [{ "title": "App", "width": 1200, "height": 800 }]`

