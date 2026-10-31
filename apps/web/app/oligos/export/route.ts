import { ApiError, apiCsv } from "@/lib/api";

export async function GET(request: Request) {
  const q = new URL(request.url).searchParams.get("q") ?? "";
  try {
    const upstream = await apiCsv(`/registry/oligos/export.csv?q=${encodeURIComponent(q)}`);
    const headers = new Headers();
    for (const name of ["Content-Type", "Content-Disposition", "X-Export-Row-Count", "X-Export-Schema"]) {
      const value = upstream.headers.get(name);
      if (value) headers.set(name, value);
    }
    headers.set("Cache-Control", "no-store");
    headers.set("X-Content-Type-Options", "nosniff");
    return new Response(upstream.body, { headers });
  } catch (error) {
    const status = error instanceof ApiError ? error.status : 503;
    const message = error instanceof ApiError ? error.message : "Export unavailable.";
    return Response.json({ error: message }, { status, headers: { "Cache-Control": "no-store" } });
  }
}
