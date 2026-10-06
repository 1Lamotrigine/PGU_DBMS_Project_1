import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const TOKEN_COOKIE = "eq_token";
const PROTECTED_PREFIXES = ["/dashboard", "/calibration", "/missions", "/levels", "/test", "/game", "/pronounce", "/admin"];

function decodePayload(token: string): { sub?: string; role?: string } | null {
  try {
    const part = token.split(".")[1];
    const json = atob(part.replace(/-/g, "+").replace(/_/g, "/"));
    return JSON.parse(json);
  } catch {
    return null;
  }
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const isProtected = PROTECTED_PREFIXES.some((p) => pathname.startsWith(p));
  if (!isProtected) return NextResponse.next();

  const token = request.cookies.get(TOKEN_COOKIE)?.value;
  if (!token) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  const payload = decodePayload(token);
  if (pathname.startsWith("/admin") && payload?.role !== "teacher") {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/calibration/:path*", "/missions/:path*", "/levels/:path*", "/test/:path*", "/game/:path*", "/pronounce/:path*", "/admin/:path*"],
};
