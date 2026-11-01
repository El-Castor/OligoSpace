"use client";

export function ConfirmRemoveButton() {
  return <button className="text-button" type="submit" onClick={(event) => {
    if (!window.confirm("Remove this membership? This user may lose access to linked resources.")) event.preventDefault();
  }}>Remove</button>;
}
