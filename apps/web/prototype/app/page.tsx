import { notFound } from "next/navigation";
import { SoftUIPrototype } from "../components/SoftUIPrototype";

export default function Page() {
  if (process.env.NODE_ENV !== "development") notFound();
  return <SoftUIPrototype />;
}
