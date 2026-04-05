/**
 * Spec constants derived from ARCHITECTURE.md Section 9.
 * Update these when the spec changes.
 */

/** Section 9.6 — Port type colour system */
export const SPEC_TYPE_COLORS: Record<string, string> = {
  Array:         '#3B82F6',
  Series:        '#22C55E',
  DataFrame:     '#F97316',
  Text:          '#A855F7',
  Artifact:      '#6B7280',
  CompositeData: '#EF4444',
  DataObject:    '#E5E7EB',
};

/** Section 9.2 — Panel default/min/max dimensions in pixels */
export const SPEC_PANEL_DEFAULTS = {
  palette:  { default: 220, min: 160, max: 400 },
  preview:  { default: 320, min: 240, max: 600 },
  bottom:   { default: 200, min: 100 },
};

/** Section 9.3 — Keyboard shortcuts */
export const SPEC_KEYBOARD_SHORTCUTS: Record<string, string> = {
  'Control+o':       'Import workflow',
  'Control+s':       'Save workflow',
  'Control+Shift+s': 'Export workflow',
  'Control+Enter':   'Run workflow',
  'Control+.':       'Stop execution',
  'Delete':          'Delete selected',
  'Backspace':       'Delete selected',
  'Control+z':       'Undo',
  'Control+y':       'Redo',
  'Control+a':       'Select all',
  'Escape':          'Deselect all',
  'Control+b':       'Toggle palette',
  'Control+d':       'Toggle preview',
  'Control+j':       'Toggle bottom panel',
  'Control+m':       'Toggle minimap',
};

/** Section 9.8 — Bottom panel tab names */
export const SPEC_BOTTOM_TABS = [
  'AI Chat', 'Config', 'Logs', 'Lineage', 'Jobs', 'Problems',
];

/** Section 9.5 — Block node design */
export const SPEC_BLOCK_NODE = {
  width: 280,
  headerElements: ['icon', 'name', 'run-button', 'restart-button'],
  stateBadgeLocation: 'footer' as const,
  inlineParamCount: 3,
};

/** Section 9.3 — Toolbar button groups */
export const SPEC_TOOLBAR_BUTTONS = {
  projectMenu: ['New', 'Open', 'Save', 'Recent Projects', 'Close Project'],
  fileOps: ['Import', 'Save', 'Export'],
  execution: ['Run', 'Pause', 'Stop', 'Reset'],
  edit: ['Delete', 'Reload Blocks'],
};
