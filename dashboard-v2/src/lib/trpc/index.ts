import { router } from "./server";
import { sessionsRouter } from "./routers/sessions";

// Main app router
export const appRouter = router({
  sessions: sessionsRouter,
});

// Export type for client
export type AppRouter = typeof appRouter;
