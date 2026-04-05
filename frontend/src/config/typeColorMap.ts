import type { TypeHierarchyEntry } from "../types/api";

export const typeColorMap: Record<string, string> = {
  Array: "#3B82F6",
  Image: "#3B82F6",
  Series: "#22C55E",
  Spectrum: "#22C55E",
  DataFrame: "#F97316",
  PeakTable: "#F97316",
  Text: "#A855F7",
  Artifact: "#6B7280",
  CompositeData: "#EF4444",
  DataObject: "#E5E7EB",
};

export function resolveTypeColor(typeNames: string[], typeHierarchy?: TypeHierarchyEntry[]): string {
  for (const name of typeNames) {
    if (typeColorMap[name]) {
      return typeColorMap[name];
    }
    if (typeHierarchy) {
      const entry = typeHierarchy.find((t) => t.name === name);
      if (entry?.base_type && typeColorMap[entry.base_type]) {
        return typeColorMap[entry.base_type];
      }
    }
  }
  return typeColorMap.DataObject;
}
