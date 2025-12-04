---
name: jwt-oauth
type: security
priority: 2
token_estimate: 600
compatible_with: [developer, senior_software_engineer]
requires: []
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# JWT/OAuth Engineering Expertise

## Specialist Profile
Authentication specialist implementing token-based auth. Expert in JWT, OAuth 2.0, and secure session management.

---

## Patterns to Follow

### JWT Best Practices (IETF 2025)
- **Short-lived access tokens**: 15 minutes max
- **RS256 (asymmetric)**: Public key verification
- **Minimal claims**: Only essential data in payload
- **No PII in tokens**: Easily decoded
- **iss/aud/exp validation**: Always verify these claims
<!-- version: jwt >= rfc9068 -->
- **JWT Access Tokens (RFC 9068)**: Standardized access token format
- **Required claims**: `iss`, `exp`, `aud`, `sub`, `client_id`, `iat`, `jti`
<!-- version: oauth >= 2.1 -->
- **OAuth 2.1**: Consolidates security best practices
- **PKCE required**: For all clients, not just public
- **No implicit flow**: Removed from spec

### Refresh Token Security
- **Rotation on use**: New refresh token each time
- **Hash before storage**: Never store plain tokens
- **Bound to client**: IP, user-agent fingerprinting
- **Revocation support**: Immediate logout capability
- **Longer expiry**: 7-30 days typical

### OAuth 2.0 Security (2025)
- **PKCE always**: Even for confidential clients
- **Authorization code flow**: Never implicit
- **State parameter**: CSRF protection
- **mTLS or private key JWT**: Client authentication
- **Exact redirect URI matching**: No wildcards

### Token Storage
- **httpOnly cookies for web**: XSS protection
- **Secure + SameSite=Strict**: CSRF protection
- **Web Workers for SPAs**: If cookies not possible
- **Never localStorage**: XSS vulnerable
- **Secure storage for mobile**: Keychain/Keystore

### Key Management
- **256-bit minimum entropy**: Cryptographically strong
- **Rotation every 30-90 days**: Limit exposure
- **JWKS endpoint**: Public key distribution
- **Overlapping validity**: Zero-downtime rotation
<!-- version: jose >= es256 -->
- **ES256 preferred**: Smaller signatures than RS256
- **EdDSA support**: Ed25519 for best performance
<!-- version: dpop >= 1.0 -->
- **DPoP (Proof of Possession)**: Sender-constrained tokens
- **Prevents token replay**: Even if intercepted

---

## Patterns to Avoid

### JWT Anti-Patterns
- ❌ **Long-lived access tokens**: Hours or days
- ❌ **HS256 with weak secret**: Easy to crack
- ❌ **Sensitive data in payload**: PII, secrets
- ❌ **No expiration validation**: Replay attacks
- ❌ **alg=none accepted**: Critical vulnerability

### Storage Anti-Patterns
- ❌ **JWT in localStorage**: XSS vulnerable
- ❌ **Plain refresh tokens in DB**: No hashing
- ❌ **Shared secrets across services**: Blast radius
- ❌ **Hardcoded secrets**: In code or config

### OAuth Anti-Patterns
- ❌ **Implicit flow**: Deprecated, insecure
- ❌ **No PKCE**: Vulnerable to interception
- ❌ **Wildcard redirects**: Open redirect attacks
- ❌ **Password grant without need**: Use auth code

### Refresh Anti-Patterns
- ❌ **No token rotation**: Stolen tokens persist
- ❌ **No revocation**: Can't invalidate on logout
- ❌ **Same expiry as access**: Defeats purpose
- ❌ **Not bound to session**: Transferable

---

## Verification Checklist

### JWT
- [ ] Access token expiry ≤15 min
- [ ] RS256 or ES256 algorithm
- [ ] iss/aud/exp validated
- [ ] No sensitive data in claims

### Refresh Tokens
- [ ] Hashed before storage
- [ ] Rotation on each use
- [ ] Revocation implemented
- [ ] Reasonable expiry (7-30 days)

### OAuth
- [ ] PKCE implemented
- [ ] Authorization code flow
- [ ] State parameter validated
- [ ] Exact redirect URI match

### Storage & Transport
- [ ] httpOnly cookies (web)
- [ ] HTTPS only
- [ ] SameSite=Strict
- [ ] Secure key management

---

## Code Patterns (Reference)

### JWT Generation
- **Sign**: `jwt.sign(payload, privateKey, { algorithm: 'RS256', expiresIn: '15m', issuer: 'api', audience: 'app' })`
- **Verify**: `jwt.verify(token, publicKey, { algorithms: ['RS256'], issuer: 'api', audience: 'app' })`

### Refresh Token
- **Generate**: `const refreshToken = crypto.randomBytes(40).toString('hex')`
- **Store**: `const hash = await argon2.hash(refreshToken); await db.refreshTokens.create({ userId, tokenHash: hash })`
- **Validate**: `await argon2.verify(storedHash, providedToken)`
- **Rotate**: `await db.refreshTokens.delete({ tokenHash: oldHash }); await db.refreshTokens.create({ tokenHash: newHash })`

### OAuth PKCE
- **Verifier**: `const verifier = crypto.randomBytes(32).toString('base64url')`
- **Challenge**: `const challenge = crypto.createHash('sha256').update(verifier).digest('base64url')`
- **Request**: `code_challenge=${challenge}&code_challenge_method=S256`

### httpOnly Cookie
- **Set**: `res.cookie('accessToken', token, { httpOnly: true, secure: true, sameSite: 'strict', maxAge: 900000 })`

