---
name: auth-patterns
type: security
priority: 2
token_estimate: 600
compatible_with: [developer, senior_software_engineer]
requires: []
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Authentication Patterns Expertise

## Specialist Profile
Authentication specialist implementing secure auth flows. Expert in OIDC, API keys, and enterprise SSO patterns.

---

## Patterns to Follow

### OpenID Connect (OIDC)
- **Authorization code + PKCE**: Modern secure flow
- **ID token validation**: iss, aud, exp, nonce
- **Userinfo endpoint**: Additional claims
- **Discovery document**: Auto-configuration
- **Session management**: RP-initiated logout

### API Key Security
- **Prefix for identification**: First 8 chars visible
- **Hash before storage**: Argon2, bcrypt
- **Scoped permissions**: Principle of least privilege
- **Expiration support**: Time-limited keys
- **Rotation capability**: Generate new, revoke old

### Multi-Factor Authentication
- **TOTP (RFC 6238)**: Time-based codes
- **WebAuthn/Passkeys**: Phishing-resistant
- **Recovery codes**: Secure backup
- **Remember device**: Risk-based MFA
- **Fallback methods**: Not just one factor

### Session Management
- **Secure session IDs**: Cryptographic random
- **Server-side storage**: Redis, database
- **Absolute timeout**: Max session duration
- **Idle timeout**: Inactivity expiration
- **Session regeneration**: After auth level change

### Enterprise SSO
- **SAML 2.0**: Enterprise standard
- **SCIM**: User provisioning
- **JIT provisioning**: Create user on first login
- **Attribute mapping**: IdP claims to app roles
- **Single logout**: Cross-application signout

---

## Patterns to Avoid

### OIDC Anti-Patterns
- ❌ **Implicit flow**: Use authorization code
- ❌ **No PKCE**: Vulnerable to interception
- ❌ **Skipping claim validation**: Trust but verify
- ❌ **Ignoring nonce**: Replay attacks

### API Key Anti-Patterns
- ❌ **Plain-text storage**: Easy to steal
- ❌ **No expiration**: Eternal access
- ❌ **Overly broad scopes**: Excessive permissions
- ❌ **Keys in URLs**: Logged, cached, visible

### Session Anti-Patterns
- ❌ **Predictable session IDs**: Sequential numbers
- ❌ **Client-side only**: No server validation
- ❌ **No timeout**: Sessions last forever
- ❌ **Fixed session ID**: No regeneration after login

### General Anti-Patterns
- ❌ **Basic auth over HTTP**: Credentials in clear
- ❌ **Shared secrets across services**: Blast radius
- ❌ **No rate limiting**: Brute force possible
- ❌ **Missing audit logs**: Can't trace access

---

## Verification Checklist

### OIDC
- [ ] Authorization code + PKCE flow
- [ ] ID token claims validated
- [ ] State parameter verified
- [ ] Logout implemented

### API Keys
- [ ] Hashed in database
- [ ] Prefix for identification
- [ ] Scoped permissions
- [ ] Rotation/revocation supported

### Sessions
- [ ] Cryptographic random IDs
- [ ] Server-side storage
- [ ] Idle and absolute timeouts
- [ ] Regeneration after login

### Security
- [ ] Rate limiting on auth endpoints
- [ ] Audit logging
- [ ] MFA available
- [ ] Secure transport (HTTPS)

---

## Code Patterns (Reference)

### OIDC (openid-client)
- **Discovery**: `const issuer = await Issuer.discover(process.env.OIDC_ISSUER_URL)`
- **PKCE**: `const verifier = generators.codeVerifier(); const challenge = generators.codeChallenge(verifier)`
- **Auth URL**: `client.authorizationUrl({ scope: 'openid profile', code_challenge: challenge, code_challenge_method: 'S256', state, nonce })`
- **Callback**: `const tokenSet = await client.callback(redirectUri, params, { code_verifier: verifier, state, nonce })`

### API Key
- **Generate**: `const rawKey = crypto.randomBytes(32).toString('base64url'); const prefix = rawKey.slice(0, 8)`
- **Store**: `await db.apiKeys.create({ prefix, hashedKey: await argon2.hash(rawKey), scopes, userId })`
- **Validate**: `const key = await db.apiKeys.findOne({ prefix }); if (await argon2.verify(key.hashedKey, rawKey)) { ... }`

### Session
- **Create**: `req.session.userId = user.id; req.session.regenerate(callback)`
- **Config**: `{ secret, resave: false, saveUninitialized: false, cookie: { secure: true, httpOnly: true, maxAge: 3600000 } }`

### SAML
- **Strategy**: `new SamlStrategy({ entryPoint, issuer, cert, callbackUrl }, (profile, done) => { ... })`

