---
name: jwt-oauth
type: security
priority: 2
token_estimate: 400
compatible_with: [developer, senior_software_engineer]
requires: []
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# JWT/OAuth Engineering Expertise

## Specialist Profile
Authentication specialist implementing token-based auth. Expert in JWT, OAuth 2.0, and session management.

## Implementation Guidelines

### JWT Token Service

```typescript
// services/tokenService.ts
import jwt from 'jsonwebtoken';
import { createHash, randomBytes } from 'crypto';

interface TokenPayload {
  sub: string;
  email: string;
  role: string;
}

export class TokenService {
  private readonly accessSecret = process.env.JWT_ACCESS_SECRET!;
  private readonly refreshSecret = process.env.JWT_REFRESH_SECRET!;

  generateAccessToken(payload: TokenPayload): string {
    return jwt.sign(payload, this.accessSecret, {
      expiresIn: '15m',
      algorithm: 'HS256',
      issuer: 'api.example.com',
      audience: 'example.com',
    });
  }

  generateRefreshToken(): string {
    return randomBytes(40).toString('hex');
  }

  verifyAccessToken(token: string): TokenPayload {
    return jwt.verify(token, this.accessSecret, {
      algorithms: ['HS256'],
      issuer: 'api.example.com',
      audience: 'example.com',
    }) as TokenPayload;
  }

  async storeRefreshToken(userId: string, token: string): Promise<void> {
    const hash = createHash('sha256').update(token).digest('hex');
    await db.refreshTokens.create({
      userId,
      tokenHash: hash,
      expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
    });
  }

  async validateRefreshToken(userId: string, token: string): Promise<boolean> {
    const hash = createHash('sha256').update(token).digest('hex');
    const stored = await db.refreshTokens.findOne({
      userId,
      tokenHash: hash,
      expiresAt: { $gt: new Date() },
    });
    return !!stored;
  }

  async revokeRefreshToken(userId: string, token: string): Promise<void> {
    const hash = createHash('sha256').update(token).digest('hex');
    await db.refreshTokens.delete({ userId, tokenHash: hash });
  }
}
```

### OAuth 2.0 Flow

```typescript
// auth/oauth.ts
import { OAuth2Client } from 'google-auth-library';

const googleClient = new OAuth2Client({
  clientId: process.env.GOOGLE_CLIENT_ID,
  clientSecret: process.env.GOOGLE_CLIENT_SECRET,
  redirectUri: process.env.GOOGLE_REDIRECT_URI,
});

export async function handleGoogleCallback(code: string) {
  const { tokens } = await googleClient.getToken(code);
  const ticket = await googleClient.verifyIdToken({
    idToken: tokens.id_token!,
    audience: process.env.GOOGLE_CLIENT_ID,
  });

  const payload = ticket.getPayload()!;

  // Find or create user
  let user = await db.users.findByEmail(payload.email!);
  if (!user) {
    user = await db.users.create({
      email: payload.email!,
      displayName: payload.name!,
      provider: 'google',
      providerId: payload.sub,
      emailVerified: payload.email_verified,
    });
  }

  // Generate tokens
  const tokenService = new TokenService();
  const accessToken = tokenService.generateAccessToken({
    sub: user.id,
    email: user.email,
    role: user.role,
  });
  const refreshToken = tokenService.generateRefreshToken();
  await tokenService.storeRefreshToken(user.id, refreshToken);

  return { accessToken, refreshToken, user };
}
```

### Auth Middleware

```typescript
// middleware/auth.ts
export function authenticate(req: Request, res: Response, next: NextFunction) {
  const authHeader = req.headers.authorization;
  if (!authHeader?.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Missing token' });
  }

  const token = authHeader.slice(7);
  try {
    const payload = tokenService.verifyAccessToken(token);
    req.user = payload;
    next();
  } catch (error) {
    if (error instanceof jwt.TokenExpiredError) {
      return res.status(401).json({ error: 'Token expired' });
    }
    return res.status(401).json({ error: 'Invalid token' });
  }
}

// Token refresh endpoint
router.post('/refresh', async (req, res) => {
  const { refreshToken } = req.body;

  const decoded = jwt.decode(req.headers.authorization?.slice(7) || '');
  if (!decoded?.sub) return res.status(401).json({ error: 'Invalid token' });

  const valid = await tokenService.validateRefreshToken(decoded.sub, refreshToken);
  if (!valid) return res.status(401).json({ error: 'Invalid refresh token' });

  // Rotate refresh token
  await tokenService.revokeRefreshToken(decoded.sub, refreshToken);
  const newRefreshToken = tokenService.generateRefreshToken();
  await tokenService.storeRefreshToken(decoded.sub, newRefreshToken);

  const accessToken = tokenService.generateAccessToken({ sub: decoded.sub, ... });
  return res.json({ accessToken, refreshToken: newRefreshToken });
});
```

## Patterns to Avoid
- ❌ Storing JWT in localStorage (use httpOnly cookies)
- ❌ Long-lived access tokens
- ❌ No refresh token rotation
- ❌ Missing token revocation

## Verification Checklist
- [ ] Short access token expiry (15m)
- [ ] Secure refresh token storage
- [ ] Token rotation on refresh
- [ ] Proper revocation
- [ ] PKCE for OAuth
