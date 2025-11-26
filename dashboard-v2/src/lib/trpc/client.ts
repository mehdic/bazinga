"use client";

import { createTRPCReact } from "@trpc/react-query";
import type { AppRouter } from "./index";

export const trpc = createTRPCReact<AppRouter>();
