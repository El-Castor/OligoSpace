import type { ScientificJobSummary } from "@/lib/api";

type ComponentFact = {
  state?: string;
  value?: number;
  units?: string;
  method?: string;
  tool_mode?: string;
};

function fact(value: unknown): ComponentFact | null {
  return typeof value === "object" && value !== null ? (value as ComponentFact) : null;
}

function object(value: unknown): Record<string, unknown> | null {
  return typeof value === "object" && value !== null
    ? (value as Record<string, unknown>)
    : null;
}

function FactCard({ label, value }: { label: string; value: unknown }) {
  const item = fact(value);
  return (
    <div className="scientific-fact">
      <span>{label}</span>
      {item?.state === "available" ? (
        <strong>
          {Number(item.value).toFixed(2)} {item.units === "degC" ? "°C" : item.units}
        </strong>
      ) : (
        <strong>{item?.state ?? "unavailable"}</strong>
      )}
      <small>
        {item?.method ?? "No method returned"}
        {item?.tool_mode ? ` · ${item.tool_mode}` : ""}
      </small>
    </div>
  );
}

export function Primer3Result({ job }: { job: ScientificJobSummary }) {
  if (!job.result) return null;
  const payload = job.result.payload;
  if (job.kind === "oligo_primer3_qc") {
    return (
      <div className="scientific-results">
        <FactCard label="Primer3 nearest-neighbor Tm" value={payload.nearest_neighbor_tm} />
        <FactCard label="Hairpin" value={payload.hairpin} />
        <FactCard label="Homodimer" value={payload.homodimer} />
      </div>
    );
  }
  const forward = object(payload.forward);
  const reverse = object(payload.reverse);
  return (
    <>
      <h3>Forward primer</h3>
      <div className="scientific-results">
        <FactCard label="Nearest-neighbor Tm" value={forward?.nearest_neighbor_tm} />
        <FactCard label="Hairpin" value={forward?.hairpin} />
        <FactCard label="Homodimer" value={forward?.homodimer} />
      </div>
      <h3>Reverse primer</h3>
      <div className="scientific-results">
        <FactCard label="Nearest-neighbor Tm" value={reverse?.nearest_neighbor_tm} />
        <FactCard label="Hairpin" value={reverse?.hairpin} />
        <FactCard label="Homodimer" value={reverse?.homodimer} />
      </div>
      <h3>Pair facts</h3>
      <div className="scientific-results">
        <FactCard label="Absolute Tm delta" value={payload.tm_delta} />
        <FactCard label="Heterodimer" value={payload.heterodimer} />
        <FactCard label="3′ end complementarity" value={payload.end_complementarity} />
      </div>
    </>
  );
}
