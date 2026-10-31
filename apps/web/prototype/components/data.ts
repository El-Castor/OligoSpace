export type DemoStatus = "Actif" | "À revoir" | "Archivé";
export type DemoOligo = {
  id: string; name: string; organism?: string; sequence: string; status: DemoStatus;
};

// Entirely fictional plant-lab examples. No mapping, real gene identifier or
// experimental validation is asserted for these synthetic sequences.
export const demoOligos: readonly DemoOligo[] = [
  { id: "DEMO-OLG-001", name: "Bd21 · floraison / F", organism: "Brachypodium distachyon", sequence: "ATGAGTGATATCGCCGTT", status: "Actif" },
  { id: "DEMO-OLG-002", name: "Bd21 · floraison / R", organism: "Brachypodium distachyon", sequence: "TTCAGCTCAGGATGACCTT", status: "Actif" },
  { id: "DEMO-OLG-003", name: "Bd21-3 · racines / F", organism: "Brachypodium distachyon", sequence: "CAGACCTCCTGGTAACTACG", status: "À revoir" },
  { id: "DEMO-OLG-004", name: "Bd21-3 · racines / R", organism: "Brachypodium distachyon", sequence: "GTTCTCAGCATTTGTCCAC", status: "Actif" },
  { id: "DEMO-OLG-005", name: "Témoin végétal / F", organism: "Arabidopsis thaliana", sequence: "TCCAGTTGCCTTGGGACT", status: "Archivé" },
  { id: "DEMO-OLG-006", name: "Témoin végétal / R", organism: "Arabidopsis thaliana", sequence: "AAGGTTGAGGTCGTGGTTG", status: "Actif" },
];
