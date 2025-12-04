---
name: rust
type: language
priority: 1
token_estimate: 500
compatible_with: [developer, senior_software_engineer]
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Rust Engineering Expertise

## Specialist Profile
Rust engineer building safe, performant systems. Expert in ownership, lifetimes, and zero-cost abstractions.

## Implementation Guidelines

### Error Handling

```rust
use thiserror::Error;

#[derive(Error, Debug)]
pub enum UserError {
    #[error("user not found: {0}")]
    NotFound(String),
    #[error("database error: {0}")]
    Database(#[from] sqlx::Error),
}

pub type Result<T> = std::result::Result<T, UserError>;

fn get_user(id: &str) -> Result<User> {
    db::find_user(id)?
        .ok_or_else(|| UserError::NotFound(id.to_string()))
}
```

### Struct Design

```rust
#[derive(Debug, Clone)]
pub struct Config {
    host: String,
    port: u16,
}

impl Config {
    pub fn new(host: impl Into<String>, port: u16) -> Result<Self, ConfigError> {
        let host = host.into();
        if host.is_empty() {
            return Err(ConfigError::EmptyHost);
        }
        Ok(Self { host, port })
    }

    pub fn host(&self) -> &str { &self.host }
}
```

### Ownership Patterns

```rust
// Take ownership when needed
fn process(data: String) -> String {
    data.to_uppercase()
}

// Borrow when you don't
fn validate(data: &str) -> bool {
    !data.is_empty()
}

// Cow for flexibility
use std::borrow::Cow;
fn normalize(input: &str) -> Cow<'_, str> {
    if input.contains(' ') {
        Cow::Owned(input.replace(' ', "_"))
    } else {
        Cow::Borrowed(input)
    }
}
```

### Async Patterns

```rust
async fn process_batch(items: Vec<Item>) -> Result<Vec<Output>> {
    let semaphore = Arc::new(Semaphore::new(10));
    let mut handles = Vec::new();

    for item in items {
        let permit = semaphore.clone().acquire_owned().await?;
        handles.push(tokio::spawn(async move {
            let result = process_item(item).await;
            drop(permit);
            result
        }));
    }

    futures::future::try_join_all(handles).await?
        .into_iter().collect()
}
```

## Patterns to Avoid
- ❌ `unwrap()` in production (use `?` or `expect()`)
- ❌ `clone()` without consideration
- ❌ Ignoring clippy warnings
- ❌ `unsafe` without justification

## Verification Checklist
- [ ] No `unwrap()` outside tests
- [ ] Error types with thiserror
- [ ] Clear ownership (own vs borrow)
- [ ] Clippy passes clean
