---
name: electron-tauri
type: framework
priority: 2
token_estimate: 400
compatible_with: [developer, senior_software_engineer]
requires: [typescript]
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Electron/Tauri Desktop Expertise

## Specialist Profile
Desktop app specialist building cross-platform apps. Expert in IPC, native APIs, and web-to-desktop patterns.

## Implementation Guidelines

### Tauri Commands

```rust
// src-tauri/src/commands/user.rs
use tauri::State;
use crate::db::Database;

#[tauri::command]
pub async fn get_users(db: State<'_, Database>) -> Result<Vec<User>, String> {
    db.get_all_users()
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn create_user(
    request: CreateUserRequest,
    db: State<'_, Database>,
) -> Result<User, String> {
    db.create_user(request)
        .await
        .map_err(|e| e.to_string())
}
```

### Frontend Invocation (Tauri)

```typescript
// src/services/userService.ts
import { invoke } from '@tauri-apps/api/tauri';

export interface User {
  id: string;
  email: string;
  displayName: string;
}

export async function getUsers(): Promise<User[]> {
  return invoke('get_users');
}

export async function createUser(request: CreateUserRequest): Promise<User> {
  return invoke('create_user', { request });
}
```

### Electron Main Process

```typescript
// electron/main.ts
import { app, BrowserWindow, ipcMain } from 'electron';

function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow.loadFile('index.html');
}

// IPC Handlers
ipcMain.handle('get-users', async () => {
  return db.getUsers();
});

ipcMain.handle('create-user', async (_event, request: CreateUserRequest) => {
  return db.createUser(request);
});
```

### Electron Preload

```typescript
// electron/preload.ts
import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('electronAPI', {
  getUsers: () => ipcRenderer.invoke('get-users'),
  createUser: (request: CreateUserRequest) =>
    ipcRenderer.invoke('create-user', request),
});
```

### Frontend (Electron)

```typescript
// src/services/userService.ts
declare global {
  interface Window {
    electronAPI: {
      getUsers: () => Promise<User[]>;
      createUser: (request: CreateUserRequest) => Promise<User>;
    };
  }
}

export const getUsers = () => window.electronAPI.getUsers();
export const createUser = (req: CreateUserRequest) =>
  window.electronAPI.createUser(req);
```

## Patterns to Avoid
- ❌ nodeIntegration: true (security risk)
- ❌ Disabled contextIsolation
- ❌ Synchronous IPC calls
- ❌ Exposing entire Node APIs

## Verification Checklist
- [ ] Context isolation enabled
- [ ] Typed IPC communication
- [ ] Async command handlers
- [ ] Proper error handling across boundary
- [ ] Security best practices
