"use client";

import { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { httpBatchLink } from "@trpc/client";
import { trpc } from "@/lib/trpc/client";
import superjson from "superjson";
import { ThemeProvider } from "next-themes";
import { useSocketQuerySync } from "@/lib/hooks/use-socket-query-sync";

// Inner component that uses the sync hook (needs to be inside tRPC provider)
function SocketQuerySyncProvider({ children }: { children: React.ReactNode }) {
  // Connect socket events to tRPC query invalidation
  // This enables real-time updates when socket is connected
  useSocketQuerySync();
  return <>{children}</>;
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 5000,
            // No global refetchInterval - smart refetch handles this per-query
            // When socket connected: no polling (events trigger invalidation)
            // When socket disconnected: components use useSmartRefetch fallback
          },
        },
      })
  );

  const [trpcClient] = useState(() =>
    trpc.createClient({
      links: [
        httpBatchLink({
          url: "/api/trpc",
          transformer: superjson,
        }),
      ],
    })
  );

  return (
    <trpc.Provider client={trpcClient} queryClient={queryClient}>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem
          disableTransitionOnChange
        >
          <SocketQuerySyncProvider>{children}</SocketQuerySyncProvider>
        </ThemeProvider>
      </QueryClientProvider>
    </trpc.Provider>
  );
}
