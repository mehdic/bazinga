---
name: express
type: framework
priority: 2
token_estimate: 450
compatible_with: [developer, senior_software_engineer]
requires: [typescript, javascript]
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Express.js Engineering Expertise

## Specialist Profile
Express specialist building Node.js APIs. Expert in middleware patterns, error handling, and TypeScript integration.

## Implementation Guidelines

### App Structure

```typescript
// app.ts
import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import { errorHandler } from './middleware/errorHandler';
import { userRouter } from './routes/users';

const app = express();

app.use(helmet());
app.use(cors());
app.use(express.json());

app.use('/api/users', userRouter);

app.use(errorHandler);

export { app };
```

### Controllers

```typescript
// controllers/userController.ts
import { Request, Response, NextFunction } from 'express';
import { userService } from '../services/userService';
import { CreateUserDto } from '../dto/user.dto';

export const userController = {
  async getAll(req: Request, res: Response, next: NextFunction) {
    try {
      const users = await userService.findAll();
      res.json(users);
    } catch (error) {
      next(error);
    }
  },

  async create(req: Request<{}, {}, CreateUserDto>, res: Response, next: NextFunction) {
    try {
      const user = await userService.create(req.body);
      res.status(201).json(user);
    } catch (error) {
      next(error);
    }
  },
};
```

### Error Handling

```typescript
// middleware/errorHandler.ts
import { Request, Response, NextFunction } from 'express';

export class AppError extends Error {
  constructor(
    public statusCode: number,
    public code: string,
    message: string,
  ) {
    super(message);
  }
}

export function errorHandler(
  err: Error,
  req: Request,
  res: Response,
  next: NextFunction,
) {
  if (err instanceof AppError) {
    return res.status(err.statusCode).json({
      error: { code: err.code, message: err.message },
    });
  }

  console.error(err);
  res.status(500).json({
    error: { code: 'INTERNAL_ERROR', message: 'Something went wrong' },
  });
}
```

### Validation Middleware

```typescript
// middleware/validate.ts
import { z, ZodSchema } from 'zod';
import { Request, Response, NextFunction } from 'express';
import { AppError } from './errorHandler';

export const validate = (schema: ZodSchema) =>
  (req: Request, res: Response, next: NextFunction) => {
    const result = schema.safeParse(req.body);
    if (!result.success) {
      throw new AppError(400, 'VALIDATION_ERROR', 'Invalid request body');
    }
    req.body = result.data;
    next();
  };

// Usage
const createUserSchema = z.object({
  email: z.string().email(),
  displayName: z.string().min(2),
});

router.post('/', validate(createUserSchema), userController.create);
```

### Async Wrapper

```typescript
// utils/asyncHandler.ts
import { Request, Response, NextFunction, RequestHandler } from 'express';

export const asyncHandler = (fn: RequestHandler): RequestHandler =>
  (req, res, next) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };

// Usage - no try/catch needed
router.get('/', asyncHandler(async (req, res) => {
  const users = await userService.findAll();
  res.json(users);
}));
```

## Patterns to Avoid
- ❌ Callback-based async (use async/await)
- ❌ Try/catch in every route (use asyncHandler)
- ❌ Business logic in routes
- ❌ Unhandled promise rejections

## Verification Checklist
- [ ] Central error handling
- [ ] Request validation
- [ ] TypeScript throughout
- [ ] Async error wrapper
- [ ] Proper status codes
