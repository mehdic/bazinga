import { test, expect } from "@playwright/test";

// Smoke tests that verify basic page structure from build output
// These are more resilient in restricted environments

test.describe("Build Output Verification", () => {
  test.beforeEach(async ({ page }) => {
    // Use longer timeout for server startup
    test.setTimeout(60000);
  });

  test("home page returns 200", async ({ request }) => {
    const response = await request.get("/");
    expect(response.status()).toBe(200);
  });

  test("sessions page returns 200", async ({ request }) => {
    const response = await request.get("/sessions");
    expect(response.status()).toBe(200);
  });

  test("analytics page returns 200", async ({ request }) => {
    const response = await request.get("/analytics");
    expect(response.status()).toBe(200);
  });

  test("settings page returns 200", async ({ request }) => {
    const response = await request.get("/settings");
    expect(response.status()).toBe(200);
  });

  test("config page returns 200", async ({ request }) => {
    const response = await request.get("/config");
    expect(response.status()).toBe(200);
  });

  test("compare page returns 200", async ({ request }) => {
    const response = await request.get("/sessions/compare");
    expect(response.status()).toBe(200);
  });

  test("tRPC endpoint exists", async ({ request }) => {
    // tRPC batch endpoint should be accessible (even if it returns an error for invalid request)
    const response = await request.get("/api/trpc/sessions.list?batch=1&input={}");
    // Should return 200 or 400 (invalid request), but NOT 404 or 500
    expect([200, 400]).toContain(response.status());
  });

  test("404 page returns proper status", async ({ request }) => {
    const response = await request.get("/non-existent-route-12345");
    expect(response.status()).toBe(404);
  });
});
