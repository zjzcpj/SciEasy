import type { TypeHierarchyEntry } from "../types/api";

export interface PortRow {
  name: string;
  types: string[];
}

interface PortEditorTableProps {
  direction: "input" | "output";
  ports: PortRow[];
  /** Type names allowed for this direction. Empty = show all from typeHierarchy. */
  allowedTypes: string[];
  typeHierarchy: TypeHierarchyEntry[];
  onChange: (ports: PortRow[]) => void;
  /** ADR-029 Addendum 1: minimum number of ports. null/undefined = no minimum. */
  minPorts?: number | null;
  /** ADR-029 Addendum 1: maximum number of ports. null/undefined = no maximum. */
  maxPorts?: number | null;
}

export function PortEditorTable({ direction, ports, allowedTypes, typeHierarchy, onChange, minPorts, maxPorts }: PortEditorTableProps) {
  const availableTypes =
    allowedTypes.length > 0
      ? typeHierarchy.filter((t) => allowedTypes.includes(t.name))
      : typeHierarchy;

  const defaultType = availableTypes[0]?.name ?? "DataObject";

  // ADR-029 Addendum 1: disable add/remove at min/max limits.
  const canAdd = maxPorts == null || ports.length < maxPorts;
  const canRemove = minPorts == null || ports.length > minPorts;

  function handleNameChange(index: number, name: string) {
    onChange(ports.map((p, i) => (i === index ? { ...p, name } : p)));
  }

  function handleTypeChange(index: number, typeName: string) {
    onChange(ports.map((p, i) => (i === index ? { ...p, types: [typeName] } : p)));
  }

  function handleRemove(index: number) {
    onChange(ports.filter((_, i) => i !== index));
  }

  function handleAdd() {
    onChange([...ports, { name: `port_${ports.length + 1}`, types: [defaultType] }]);
  }

  return (
    <div className="mb-4">
      <h3 className="mb-2 text-sm font-semibold text-ink">
        {direction === "input" ? "Input Ports" : "Output Ports"}
      </h3>
      <div className="flex flex-col gap-1.5">
        {ports.map((port, index) => (
          <div className="flex items-center gap-2" key={port.name + '-' + index}>
            <input
              className="w-32 rounded-xl border border-stone-300 bg-white px-3 py-1.5 text-sm"
              onChange={(e) => handleNameChange(index, e.target.value)}
              placeholder="port name"
              value={port.name}
            />
            <select
              className="min-w-0 flex-1 rounded-xl border border-stone-300 bg-white px-3 py-1.5 text-sm"
              onChange={(e) => handleTypeChange(index, e.target.value)}
              value={port.types[0] ?? defaultType}
            >
              {availableTypes.length > 0 ? (
                availableTypes.map((t) => (
                  <option key={t.name} value={t.name}>
                    {t.name}
                  </option>
                ))
              ) : (
                <option value="DataObject">DataObject</option>
              )}
            </select>
            <button
              className={`rounded-lg px-2 py-1 text-xs ${canRemove ? "text-stone-500 hover:bg-red-100 hover:text-red-700" : "cursor-not-allowed text-stone-300"}`}
              disabled={!canRemove}
              onClick={() => handleRemove(index)}
              title={canRemove ? "Remove port" : `Minimum ${minPorts} port(s) required`}
              type="button"
            >
              −
            </button>
          </div>
        ))}
        {ports.length === 0 && (
          <p className="text-xs text-stone-400">No ports defined. Click &quot;+ Add Port&quot; to add one.</p>
        )}
      </div>
      <button
        className={`mt-2 rounded-xl border px-3 py-1.5 text-sm ${canAdd ? "border-stone-300 bg-white text-stone-600 hover:bg-stone-50" : "cursor-not-allowed border-stone-200 bg-stone-50 text-stone-400"}`}
        disabled={!canAdd}
        onClick={handleAdd}
        title={canAdd ? undefined : `Maximum ${maxPorts} port(s) allowed`}
        type="button"
      >
        + Add Port
      </button>
    </div>
  );
}
