import type { TypeHierarchyEntry } from "../types/api";

// ---------------------------------------------------------------------------
// Base type color palette (#445)
// ---------------------------------------------------------------------------
export const typeColorMap: Record<string, string> = {
  Array: "#3b82f6",
  Image: "#3b82f6",
  Series: "#14b8a6",
  Spectrum: "#14b8a6",
  DataFrame: "#f59e0b",
  PeakTable: "#f59e0b",
  Text: "#22c55e",
  Artifact: "#6b7280",
  CompositeData: "#8b5cf6",
  Label: "#8b5cf6",
  Mask: "#3b82f6",
  DataObject: "#e5e7eb",
};

// ---------------------------------------------------------------------------
// Subtype ring color map — subtypes that get a contrasting ring (#445)
// Key = type name, value = ring (border) color.
// ---------------------------------------------------------------------------
export const subtypeRingColorMap: Record<string, string> = {
  Image: "#ef4444",
  Label: "#ef4444",
  Mask: "#ec4899",
  Spectrum: "#ef4444",
  PeakTable: "#ef4444",
};

/**
 * Resolve the fill color for a port given its accepted_types list and
 * optional type hierarchy from the schema.
 */
export function resolveTypeColor(
  typeNames: string[],
  typeHierarchy?: TypeHierarchyEntry[],
): string {
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

/**
 * Resolve the ring (border) color for a subtype port. Returns `undefined`
 * for base types that should not have a contrasting ring.
 */
export function resolveRingColor(
  typeNames: string[],
  typeHierarchy?: TypeHierarchyEntry[],
): string | undefined {
  for (const name of typeNames) {
    // Check explicit ring colors first
    if (subtypeRingColorMap[name]) {
      return subtypeRingColorMap[name];
    }
    // Check backend-supplied ui_ring_color
    if (typeHierarchy) {
      const entry = typeHierarchy.find((t) => t.name === name);
      if (entry?.ui_ring_color) {
        return entry.ui_ring_color;
      }
    }
  }
  return undefined;
}

/**
 * Check whether a port represents the "Any" type (empty accepted_types).
 */
export function isAnyType(typeNames: string[]): boolean {
  return typeNames.length === 0;
}

/**
 * Get the primary display type name for a port.
 */
export function primaryTypeName(typeNames: string[]): string {
  if (typeNames.length === 0) return "Any";
  return typeNames[0];
}
