import Link from "next/link";

export function RegistrySearch({ action, query }: { action: string; query: string }) {
  return (
    <form className="registry-search" action={action} role="search">
      <label htmlFor="registry-query">Search this registry</label>
      <div className="registry-search-row">
        <input id="registry-query" name="q" defaultValue={query} placeholder="Name, public ID, sequence or identifier" />
        <button className="secondary-button" type="submit">Search</button>
        {query ? <Link className="text-link" href={action}>Clear</Link> : null}
      </div>
      {query ? <p className="active-query">Active search: <strong>{query}</strong></p> : null}
    </form>
  );
}
