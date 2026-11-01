import Link from "next/link";
import { CopyValue } from "@/components/CopyValue";

export function ScientificValue({ value, href, copy = false, sequence = false }: { value: string; href?: string; copy?: boolean; sequence?: boolean }) {
  const long = value.length > (sequence ? 16 : 24);
  const preview = `value-preview${long ? "" : " value-complete"}`;
  return <span className={`scientific-value${sequence ? " sequence" : ""}`}>
    <span className="value-line">{href ? <Link className={`row-link ${preview}`} href={href}>{value}</Link> : <span className={preview}>{value}</span>}
      {copy ? <CopyValue value={value} label={sequence ? "Copy DNA sequence" : `Copy ${value}`} /> : null}</span>
    {long ? <details className="full-value"><summary>Full value</summary><span>{value}</span></details> : null}
  </span>;
}
