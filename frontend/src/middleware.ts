import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const TOKEN_COOKIE = "eq_token";
const PROTECTED_PREFIXES = ["/dashboard", "/calibration", "/missions", "/levels", "/test", "/game", "/pronounce", "/admin"];

type JwtPayload = { sub?: string; role?: string; exp?: number };

function base64UrlToBytes(input: string): Uint8Array {
  const b64 = input.replace(/-/g, "+").replace(/_/g, "/");
  const pad = b64.length % 4 === 0 ? "" : "=".repeat(4 - (b64.length % 4));
  const bin = atob(b64 + pad);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return bytes;
}

/**
 * Verify an HS256 JWT signature and expiry. Returns the payload only when the
 * token is cryptographically valid — a forged cookie cannot pass this.
 */
async function verifyJwt(token: string, secret: string): Promise<JwtPayload | null> {
  const parts = token.split(".");
  if (parts.length !== 3) return null;
  const [header, payload, signature] = parts;
  try {
    const key = await crypto.subtle.importKey(
      "raw",
      new TextEncoder().encode(secret),
      { name: "HMAC", hash: "SHA-256" },
      false,
      ["verify"],
    );
    const data = new TextEncoder().encode(`${header}.${payload}`);
    const valid = await crypto.subtle.verify("HMAC", key, base64UrlToBytes(signature), data);
    if (!valid) return null;
    const json = JSON.parse(new TextDecoder().decode(base64UrlToBytes(payload))) as JwtPayload;
    if (json.exp && Date.now() >= json.exp * 1000) return null;
    return json;
  } catch {
    return null;
  }
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const isProtected = PROTECTED_PREFIXES.some((p) => pathname.startsWith(p));
  if (!isProtected) return NextResponse.next();

  const token = request.cookies.get(TOKEN_COOKIE)?.value;
  if (!token) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  const secret = process.env.JWT_SECRET;
  let payload: JwtPayload | null = null;
  if (secret) {
    payload = await verifyJwt(token, secret);
    if (!payload) {
      const res = NextResponse.redirect(new URL("/login", request.url));
      res.cookies.delete(TOKEN_COOKIE);
      return res;
    }
  } else {
    // No secret configured (dev): best-effort decode for UX only. The API still
    // enforces authentication and RBAC.
    try {
      payload = JSON.parse(
        new TextDecoder().decode(base64UrlToBytes(token.split(".")[1])),
      ) as JwtPayload;
    } catch {
      payload = null;
    }
  }

  if (pathname.startsWith("/admin") && payload?.role !== "teacher") {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/calibration/:path*", "/missions/:path*", "/levels/:path*", "/test/:path*", "/game/:path*", "/pronounce/:path*", "/admin/:path*"],
};
