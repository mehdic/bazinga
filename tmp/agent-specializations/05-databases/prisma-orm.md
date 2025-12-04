---
name: prisma-orm
type: database
priority: 2
token_estimate: 400
compatible_with: [developer, senior_software_engineer]
requires: [typescript]
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Prisma ORM Engineering Expertise

## Specialist Profile
Prisma specialist building type-safe database access. Expert in schema design, relations, and query optimization.

## Implementation Guidelines

### Schema Definition

```prisma
// prisma/schema.prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model User {
  id          String   @id @default(uuid())
  email       String   @unique
  displayName String   @map("display_name")
  status      Status   @default(PENDING)
  profile     Profile?
  orders      Order[]
  createdAt   DateTime @default(now()) @map("created_at")
  updatedAt   DateTime @updatedAt @map("updated_at")

  @@index([status, createdAt(sort: Desc)])
  @@map("users")
}

model Profile {
  id     String  @id @default(uuid())
  avatar String?
  bio    String?
  user   User    @relation(fields: [userId], references: [id], onDelete: Cascade)
  userId String  @unique @map("user_id")

  @@map("profiles")
}

enum Status {
  ACTIVE
  INACTIVE
  PENDING
}
```

### Repository Pattern

```typescript
// repositories/userRepository.ts
import { PrismaClient, Prisma, User, Status } from '@prisma/client';

const prisma = new PrismaClient();

export const userRepository = {
  async findAll(params: {
    status?: Status;
    cursor?: string;
    take?: number;
  }): Promise<User[]> {
    return prisma.user.findMany({
      where: { status: params.status },
      take: params.take || 20,
      skip: params.cursor ? 1 : 0,
      cursor: params.cursor ? { id: params.cursor } : undefined,
      orderBy: { createdAt: 'desc' },
      include: { profile: true },
    });
  },

  async findById(id: string) {
    return prisma.user.findUnique({
      where: { id },
      include: { profile: true, orders: { take: 10 } },
    });
  },

  async create(data: Prisma.UserCreateInput) {
    return prisma.user.create({
      data: {
        ...data,
        profile: { create: {} },
      },
      include: { profile: true },
    });
  },

  async updateStatus(id: string, status: Status) {
    return prisma.user.update({
      where: { id },
      data: { status },
    });
  },
};
```

### Transactions

```typescript
// Complex transaction
async function createUserWithOrder(
  userData: Prisma.UserCreateInput,
  orderData: Omit<Prisma.OrderCreateInput, 'user'>
) {
  return prisma.$transaction(async (tx) => {
    const user = await tx.user.create({
      data: {
        ...userData,
        profile: { create: {} },
      },
    });

    const order = await tx.order.create({
      data: {
        ...orderData,
        user: { connect: { id: user.id } },
      },
    });

    return { user, order };
  });
}
```

### Raw Queries (When Needed)

```typescript
// Complex analytics
const stats = await prisma.$queryRaw<UserStats[]>`
  SELECT
    status,
    COUNT(*)::int as count,
    DATE_TRUNC('day', created_at) as day
  FROM users
  WHERE created_at > ${startDate}
  GROUP BY status, DATE_TRUNC('day', created_at)
  ORDER BY day DESC
`;
```

## Patterns to Avoid
- ❌ N+1 queries (use include/select)
- ❌ Fetching entire relations
- ❌ Raw queries for simple operations
- ❌ Missing indexes on filtered fields

## Verification Checklist
- [ ] Proper relations defined
- [ ] Indexes on query fields
- [ ] Select only needed fields
- [ ] Transactions for multi-operation
- [ ] Migration history maintained
