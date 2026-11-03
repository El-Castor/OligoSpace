import { getToken } from "next-auth/jwt";
import { NextRequest, NextResponse } from "next/server";

import { developmentAuth, providerConfig } from "@/lib/auth";
import { endProviderSession, validLogoutRequest } from "@/lib/auth-session";

export async function POST(request: NextRequest) {
  if (!validLogoutRequest(request.headers.get("origin"), request.headers.get("content-type"),
    process.env.NEXTAUTH_URL ?? "http://oligospace.localhost:8080")) {
    return NextResponse.json({ code: "invalid_logout_request" }, { status: 403 });
  }
  const token = await getToken({ req: request, secret: process.env.NEXTAUTH_SECRET });
  if (!token) return NextResponse.json({ code: "authentication_required" }, { status: 401 });
  if (!developmentAuth && !await endProviderSession(token, providerConfig)) {
    return NextResponse.json({ code: "provider_logout_not_confirmed" }, { status: 503 });
  }
  return new NextResponse(null, { status: 204 });
}
