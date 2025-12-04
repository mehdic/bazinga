---
name: auth-patterns
type: security
priority: 2
token_estimate: 500
compatible_with: [developer, senior_software_engineer]
requires: []
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Authentication Patterns Expertise

## Specialist Profile
Authentication specialist implementing secure auth flows. Expert in OIDC, OAuth 2.0, API keys, and enterprise SSO patterns.

## Implementation Guidelines

### OpenID Connect (OIDC)

```typescript
// OIDC with Authorization Code + PKCE
import { generators, Issuer } from 'openid-client';

async function setupOIDC() {
  const issuer = await Issuer.discover(process.env.OIDC_ISSUER_URL!);

  const client = new issuer.Client({
    client_id: process.env.OIDC_CLIENT_ID!,
    client_secret: process.env.OIDC_CLIENT_SECRET,
    redirect_uris: [process.env.OIDC_REDIRECT_URI!],
    response_types: ['code'],
    token_endpoint_auth_method: 'client_secret_basic',
  });

  return client;
}

// Authorization endpoint
app.get('/auth/login', async (req, res) => {
  const codeVerifier = generators.codeVerifier();
  const codeChallenge = generators.codeChallenge(codeVerifier);
  const state = generators.state();
  const nonce = generators.nonce();

  // Store in session
  req.session.oidc = { codeVerifier, state, nonce };

  const authUrl = client.authorizationUrl({
    scope: 'openid profile email',
    code_challenge: codeChallenge,
    code_challenge_method: 'S256',
    state,
    nonce,
  });

  res.redirect(authUrl);
});

// Callback handler
app.get('/auth/callback', async (req, res) => {
  const { codeVerifier, state, nonce } = req.session.oidc;

  const params = client.callbackParams(req);
  const tokenSet = await client.callback(
    process.env.OIDC_REDIRECT_URI!,
    params,
    { code_verifier: codeVerifier, state, nonce }
  );

  // Validate ID token claims
  const claims = tokenSet.claims();
  if (claims.aud !== process.env.OIDC_CLIENT_ID) {
    throw new Error('Invalid audience');
  }

  // Create session
  const user = await findOrCreateUser(claims);
  req.session.userId = user.id;

  res.redirect('/dashboard');
});
```

### OAuth 2.0 Flows

```typescript
// Client Credentials (machine-to-machine)
async function getM2MToken(): Promise<string> {
  const response = await fetch(`${OAUTH_SERVER}/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type: 'client_credentials',
      client_id: process.env.CLIENT_ID!,
      client_secret: process.env.CLIENT_SECRET!,
      scope: 'api:read api:write',
    }),
  });

  const data = await response.json();
  return data.access_token;
}

// Resource Owner Password (legacy - avoid if possible)
async function passwordGrant(username: string, password: string) {
  const response = await fetch(`${OAUTH_SERVER}/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type: 'password',
      client_id: process.env.CLIENT_ID!,
      username,
      password,
      scope: 'openid profile',
    }),
  });

  return response.json();
}
```

### API Key Authentication

```typescript
// API Key management
interface ApiKey {
  id: string;
  hashedKey: string;
  prefix: string;  // First 8 chars for identification
  name: string;
  scopes: string[];
  userId: string;
  expiresAt: Date | null;
  lastUsedAt: Date | null;
}

async function generateApiKey(userId: string, name: string, scopes: string[]): Promise<string> {
  // Generate cryptographically secure key
  const rawKey = crypto.randomBytes(32).toString('base64url');
  const prefix = rawKey.slice(0, 8);
  const hashedKey = await argon2.hash(rawKey);

  await db.apiKeys.create({
    id: crypto.randomUUID(),
    hashedKey,
    prefix,
    name,
    scopes,
    userId,
    expiresAt: null,
    lastUsedAt: null,
  });

  // Return full key only once - user must store it
  return `${prefix}_${rawKey}`;
}

// API Key middleware
async function apiKeyAuth(req: Request, res: Response, next: NextFunction) {
  const authHeader = req.headers['x-api-key'];
  if (!authHeader) return res.status(401).json({ error: 'API key required' });

  const [prefix] = authHeader.split('_');
  const apiKey = await db.apiKeys.findOne({ prefix });

  if (!apiKey) return res.status(401).json({ error: 'Invalid API key' });
  if (apiKey.expiresAt && apiKey.expiresAt < new Date()) {
    return res.status(401).json({ error: 'API key expired' });
  }

  const valid = await argon2.verify(apiKey.hashedKey, authHeader);
  if (!valid) return res.status(401).json({ error: 'Invalid API key' });

  // Update last used
  await db.apiKeys.update(apiKey.id, { lastUsedAt: new Date() });

  req.apiKey = apiKey;
  req.scopes = apiKey.scopes;
  next();
}
```

### Basic Authentication

```typescript
// Basic Auth (use only over HTTPS, for simple APIs)
function basicAuth(req: Request, res: Response, next: NextFunction) {
  const authHeader = req.headers.authorization;
  if (!authHeader?.startsWith('Basic ')) {
    res.setHeader('WWW-Authenticate', 'Basic realm="API"');
    return res.status(401).json({ error: 'Authentication required' });
  }

  const base64 = authHeader.slice(6);
  const decoded = Buffer.from(base64, 'base64').toString('utf-8');
  const [username, password] = decoded.split(':');

  // Validate credentials (use constant-time comparison)
  const user = await validateCredentials(username, password);
  if (!user) {
    return res.status(401).json({ error: 'Invalid credentials' });
  }

  req.user = user;
  next();
}
```

### SAML SSO

```typescript
// SAML 2.0 with passport-saml
import { Strategy as SamlStrategy } from 'passport-saml';

passport.use(new SamlStrategy({
    entryPoint: process.env.SAML_ENTRY_POINT,
    issuer: process.env.SAML_ISSUER,
    cert: process.env.SAML_CERT,
    callbackUrl: process.env.SAML_CALLBACK_URL,
    identifierFormat: 'urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress',
  },
  async (profile, done) => {
    const user = await findOrCreateSamlUser({
      email: profile.email,
      nameId: profile.nameID,
      displayName: profile.displayName,
    });
    done(null, user);
  }
));

// Initiate SAML login
app.get('/auth/saml/login', passport.authenticate('saml'));

// Handle SAML response
app.post('/auth/saml/callback',
  passport.authenticate('saml', { failureRedirect: '/login' }),
  (req, res) => res.redirect('/dashboard')
);
```

## Patterns to Avoid
- ❌ Storing plain-text API keys
- ❌ OIDC without PKCE
- ❌ Basic Auth over HTTP
- ❌ Missing token validation

## Verification Checklist
- [ ] PKCE for authorization code flow
- [ ] API keys hashed and prefixed
- [ ] Token validation (iss, aud, exp)
- [ ] Secure token storage
- [ ] Rate limiting on auth endpoints
