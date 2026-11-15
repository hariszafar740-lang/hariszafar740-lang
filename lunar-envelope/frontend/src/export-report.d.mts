import type {PlanSnapshot} from './Explore';

export function buildExport(
  current: PlanSnapshot,
  baseline: PlanSnapshot | null,
  exportedAt?: string
): unknown;
