---
name: mongodb
type: database
priority: 2
token_estimate: 400
compatible_with: [developer, senior_software_engineer]
requires: []
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# MongoDB Engineering Expertise

## Specialist Profile
MongoDB specialist designing document databases. Expert in aggregation pipelines, schema design, and performance tuning.

## Implementation Guidelines

### Schema Design

```typescript
// models/User.ts
import { Schema, model, Types } from 'mongoose';

interface IUser {
  _id: Types.ObjectId;
  email: string;
  displayName: string;
  status: 'active' | 'inactive' | 'pending';
  profile: {
    avatar?: string;
    bio?: string;
  };
  createdAt: Date;
  updatedAt: Date;
}

const userSchema = new Schema<IUser>(
  {
    email: { type: String, required: true, unique: true, lowercase: true },
    displayName: { type: String, required: true, minLength: 2 },
    status: { type: String, enum: ['active', 'inactive', 'pending'], default: 'pending' },
    profile: {
      avatar: String,
      bio: { type: String, maxLength: 500 },
    },
  },
  { timestamps: true }
);

userSchema.index({ status: 1, createdAt: -1 });
userSchema.index({ email: 'text', displayName: 'text' });

export const User = model<IUser>('User', userSchema);
```

### Aggregation Pipelines

```typescript
// Get user stats with orders
const stats = await User.aggregate([
  { $match: { status: 'active' } },
  {
    $lookup: {
      from: 'orders',
      localField: '_id',
      foreignField: 'userId',
      as: 'orders',
    },
  },
  {
    $addFields: {
      orderCount: { $size: '$orders' },
      totalSpent: { $sum: '$orders.amount' },
    },
  },
  { $project: { orders: 0, password: 0 } },
  { $sort: { totalSpent: -1 } },
  { $limit: 100 },
]);

// Group by date
const dailySignups = await User.aggregate([
  {
    $group: {
      _id: { $dateToString: { format: '%Y-%m-%d', date: '$createdAt' } },
      count: { $sum: 1 },
    },
  },
  { $sort: { _id: 1 } },
]);
```

### Transactions

```typescript
const session = await mongoose.startSession();
try {
  session.startTransaction();

  const user = await User.create([{ email, displayName }], { session });
  await Profile.create([{ userId: user[0]._id }], { session });
  await sendWelcomeEmail(user[0].email);

  await session.commitTransaction();
  return user[0];
} catch (error) {
  await session.abortTransaction();
  throw error;
} finally {
  session.endSession();
}
```

### Query Optimization

```typescript
// Efficient pagination with cursor
const users = await User.find({
  status: 'active',
  _id: { $gt: lastId }, // cursor-based
})
  .select('email displayName createdAt')
  .sort({ _id: 1 })
  .limit(20)
  .lean(); // Returns plain objects

// Bulk operations
const bulkOps = users.map((user) => ({
  updateOne: {
    filter: { _id: user._id },
    update: { $set: { status: 'inactive' } },
  },
}));
await User.bulkWrite(bulkOps);
```

## Patterns to Avoid
- ❌ Unbounded arrays in documents
- ❌ Missing indexes on query fields
- ❌ Skip-based pagination at scale
- ❌ Storing related data separately without reason

## Verification Checklist
- [ ] Appropriate schema design
- [ ] Indexes match query patterns
- [ ] Aggregation for complex queries
- [ ] Lean queries where applicable
- [ ] Transactions for multi-document ops
