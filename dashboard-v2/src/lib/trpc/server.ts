import { initTRPC } from "@trpc/server";
import superjson from "superjson";

// Create tRPC instance
const t = initTRPC.create({
  transformer: superjson,
});

// Export reusable router and procedure helpers
export const router = t.router;
export const publicProcedure = t.procedure;
export const createCallerFactory = t.createCallerFactory;
