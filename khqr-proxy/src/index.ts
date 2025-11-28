import { Hono } from "hono";
import type { Context } from "hono";

// Declare process for Bun/edge type gaps if @types/node not installed
declare const process: any;

// Simple helper to mask secrets in diagnostics
const mask = (val?: string) => {
  if (!val) return 'MISSING';
  if (val.length < 12) return val;
  return `${val.slice(0,6)}…${val.slice(-4)}`;
};

const app = new Hono();

// Environment variables for API key protection and logging
const API_KEY = process.env.PROXY_API_KEY || "default-key";
const BAKONG_TOKEN = process.env.BAKONG_TOKEN; // Optional: attach auth for Bakong endpoints
const BAKONG_API_URL = "https://api-bakong.nbc.gov.kh";
const PORT = process.env.PORT || 3000;

// Middleware: verify API key
const verifyApiKey = (c: Context, next: () => Promise<void>) => {
  const key = c.req.header("X-API-KEY");
  if (!key || key !== API_KEY) {
    return c.json({ error: "Invalid or missing API key" }, 401);
  }
  return next();
};

// Unprotected health & diagnostics endpoints (do not expose sensitive data)
app.get('/health', (c: Context) => c.json({ ok: true, service: 'khqr-proxy', time: new Date().toISOString() }));
app.get('/diagnostic', (c: Context) => c.json({
  ok: true,
  masked_api_key: mask(API_KEY),
  bakong_api_url: BAKONG_API_URL,
  port: PORT,
  env_proxy_key_present: !!process.env.PROXY_API_KEY,
}));
app.get('/public-ip', async (c: Context) => {
  try {
    const resp = await fetch('https://api.ipify.org?format=json');
    const data = await resp.json();
    return c.json({ ok: true, ip: data.ip, source: 'api.ipify.org', time: new Date().toISOString() });
  } catch (err) {
    const error = err as Error;
    return c.json({ ok: false, error: 'Failed to fetch public IP', details: error.message }, 500);
  }
});

// Apply API key verification to all Bakong-routed paths only
app.use("/v1/*", verifyApiKey);
app.use("/*", verifyApiKey); // fallback for other protected paths

// Proxy all requests to Bakong API
app.all("*", async (c: Context) => {
  try {
    const path = c.req.path;
    const method = c.req.method;
    const query = c.req.query();

    // Build the full URL to forward
    const queryString = new URLSearchParams(query).toString();
    const fullUrl = `${BAKONG_API_URL}${path}${queryString ? "?" + queryString : ""}`;

    console.log(`[PROXY] ${method} ${path} -> ${fullUrl}`);

    // Build sanitized headers to avoid leaking original client IP (Railway) to Bakong
    const incoming = c.req.header();
    const headers = new Headers();
    const skip = new Set([
      'x-forwarded-for',
      'x-forwarded-host',
      'x-forwarded-port',
      'x-forwarded-proto',
      'x-real-ip',
      'cf-connecting-ip',
      'cf-ray',
      'true-client-ip'
    ]);
    for (const [k, v] of Object.entries(incoming)) {
      if (!skip.has(k.toLowerCase())) headers.set(k, v as string);
    }
    headers.set('host', 'api-bakong.nbc.gov.kh');
    if (BAKONG_TOKEN && !headers.has('authorization')) {
      headers.set('authorization', `Bearer ${BAKONG_TOKEN}`);
    }
    // Explicitly set accept/content-type if missing
    if (!headers.has('accept')) headers.set('accept', 'application/json');

    // Get the body for POST/PUT requests
    let body = null;
    if (["POST", "PUT", "PATCH"].includes(method)) {
      try {
        body = await c.req.raw.clone().text();
      } catch (e) {
        // No body
      }
    }

    // Forward the request
    const res = await fetch(fullUrl, {
      method,
      headers,
      body,
    });

    // Read the response
    const responseText = await res.text();
    console.log(`[PROXY] Response status: ${res.status} for ${method} ${path}`);

    // Return the response with the same headers
    const responseHeaders = new Headers(res.headers);
    responseHeaders.delete("content-encoding"); // Let Hono handle compression

    return new Response(responseText, {
      status: res.status,
      statusText: res.statusText,
      headers: responseHeaders,
    });
  } catch (err) {
    const error = err as Error;
    console.error("[PROXY] Error:", error.message);
    return c.json(
      { error: "Proxy error", details: error.message },
      500
    );
  }
});

console.log(`KHQR Proxy listening on port ${PORT}`);

export default {
  port: PORT,
  fetch: app.fetch,
};
