export const typeColorMap: Record<string, string> = {
  DataObject: "#2d7891",
  Array: "#2e5d50",
  Image: "#2e5d50",
  Series: "#f06a44",
  Spectrum: "#f06a44",
  DataFrame: "#8c5a2b",
  Text: "#6f5b8a",
  Artifact: "#46555f",
  CompositeData: "#b24968",
};

export function resolveTypeColor(typeNames: string[]): string {
  for (const name of typeNames) {
    if (typeColorMap[name]) {
      return typeColorMap[name];
    }
  }
  return "#2d7891";
}
