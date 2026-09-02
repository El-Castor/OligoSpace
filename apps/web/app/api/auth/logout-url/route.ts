import { NextResponse } from "next/server";

import { providerLogoutUrl } from "@/lib/auth";

export async function GET() {
  return NextResponse.json({ url: providerLogoutUrl() });
}
