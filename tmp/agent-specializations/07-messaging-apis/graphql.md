---
name: graphql
type: api
priority: 2
token_estimate: 450
compatible_with: [developer, senior_software_engineer]
requires: [typescript]
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# GraphQL Engineering Expertise

## Specialist Profile
GraphQL specialist building flexible APIs. Expert in schema design, resolvers, and performance optimization.

## Implementation Guidelines

### Schema Definition

```graphql
# schema.graphql
type Query {
  user(id: ID!): User
  users(filter: UserFilter, pagination: PaginationInput): UserConnection!
}

type Mutation {
  createUser(input: CreateUserInput!): CreateUserPayload!
  updateUser(id: ID!, input: UpdateUserInput!): UpdateUserPayload!
}

type User implements Node {
  id: ID!
  email: String!
  displayName: String!
  status: UserStatus!
  orders(first: Int, after: String): OrderConnection!
  createdAt: DateTime!
}

type UserConnection {
  edges: [UserEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type UserEdge {
  node: User!
  cursor: String!
}

input CreateUserInput {
  email: String!
  displayName: String!
}

type CreateUserPayload {
  user: User
  errors: [Error!]
}

enum UserStatus {
  ACTIVE
  INACTIVE
  PENDING
}
```

### Resolvers

```typescript
// resolvers/user.ts
import { Resolvers } from '../generated/graphql';

export const userResolvers: Resolvers = {
  Query: {
    user: async (_, { id }, { dataSources }) => {
      return dataSources.userAPI.getById(id);
    },
    users: async (_, { filter, pagination }, { dataSources }) => {
      const { nodes, totalCount, hasNextPage } =
        await dataSources.userAPI.list({ filter, ...pagination });

      return {
        edges: nodes.map((node) => ({
          node,
          cursor: encodeCursor(node.id),
        })),
        pageInfo: {
          hasNextPage,
          endCursor: nodes.length ? encodeCursor(nodes.at(-1)!.id) : null,
        },
        totalCount,
      };
    },
  },

  Mutation: {
    createUser: async (_, { input }, { dataSources }) => {
      try {
        const user = await dataSources.userAPI.create(input);
        return { user, errors: null };
      } catch (error) {
        return { user: null, errors: [formatError(error)] };
      }
    },
  },

  User: {
    orders: async (parent, args, { dataSources }) => {
      return dataSources.orderAPI.getByUserId(parent.id, args);
    },
  },
};
```

### DataLoader for N+1

```typescript
// dataloaders/userLoader.ts
import DataLoader from 'dataloader';

export function createUserLoader(db: Database) {
  return new DataLoader<string, User>(async (ids) => {
    const users = await db.users.findMany({
      where: { id: { in: [...ids] } },
    });

    const userMap = new Map(users.map((u) => [u.id, u]));
    return ids.map((id) => userMap.get(id) ?? null);
  });
}

// Context setup
export function createContext({ req }: { req: Request }) {
  return {
    userLoader: createUserLoader(db),
    currentUser: req.user,
  };
}

// Usage in resolver
User: {
  organization: (parent, _, { userLoader }) => {
    return userLoader.load(parent.organizationId);
  },
}
```

### Input Validation

```typescript
// directives/validation.ts
import { mapSchema, getDirective, MapperKind } from '@graphql-tools/utils';
import { GraphQLError } from 'graphql';

export function validationDirective(schema: GraphQLSchema) {
  return mapSchema(schema, {
    [MapperKind.INPUT_OBJECT_FIELD]: (fieldConfig, fieldName, typeName) => {
      const constraint = getDirective(schema, fieldConfig, 'constraint')?.[0];
      if (constraint) {
        const { resolve = defaultFieldResolver } = fieldConfig;
        fieldConfig.resolve = async (source, args, context, info) => {
          const value = source[fieldName];
          if (constraint.minLength && value.length < constraint.minLength) {
            throw new GraphQLError(`${fieldName} must be at least ${constraint.minLength} characters`);
          }
          return resolve(source, args, context, info);
        };
      }
      return fieldConfig;
    },
  });
}
```

## Patterns to Avoid
- ❌ N+1 queries (use DataLoader)
- ❌ Unbounded list queries
- ❌ Over-fetching in resolvers
- ❌ Missing error handling

## Verification Checklist
- [ ] DataLoader for batching
- [ ] Cursor-based pagination
- [ ] Input validation
- [ ] Error payload pattern
- [ ] Query complexity limits
