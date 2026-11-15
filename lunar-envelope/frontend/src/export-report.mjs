import {describeChanges} from './comparison.mjs';

// Preserve the complete API response rather than reconstructing science inputs.
export function buildExport(current, baseline, exportedAt = new Date().toISOString()) {
  return {
    schema: 'lunaris-site-comparison-v1',
    exported_at_utc: exportedAt,
    notice: 'Exploratory screening only; not flight qualified. No terrain, antenna or operational constraints.',
    manifest: {
      report_type: 'spherical-geometric-site-comparison',
      snapshot: 'Last successful comparison, not pending form edits.',
      time_standard: 'UTC',
      code_revision: null,
      code_revision_note: 'Not captured automatically; record the deployed repository commit separately.',
      terrain: 'Not included; optional terrain screening has a separate JSON export.',
      interpretation: 'Midpoint-bin counts and selected sensitivity tests are not operational windows or uncertainty bounds.',
      provenance: 'See current.provenance_url, current.assumptions, current.limits, model version and dataset SHA-256 in this report.'
    },
    current,
    baseline,
    change_summary: baseline ? describeChanges(baseline, current) : null
  };
}
