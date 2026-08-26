import { PageHeader } from "@/components/PageHeader";

export function PlannedPage({ title, description }: { title: string; description: string }) {
  return (
    <>
      <PageHeader eyebrow="Planned workflow" title={title} description={description} />
      <section className="planned-page">
        <h2>Designed, not represented as complete</h2>
        <p>
          The data boundary and navigation slot are reserved. Implementation is tracked in the project
          backlog and will arrive with authorization, audit, migrations, and tests as one coherent phase.
        </p>
      </section>
    </>
  );
}
