import type {PlanSnapshot} from './Explore';

export function describeChanges(base: PlanSnapshot, current: PlanSnapshot): {
  inputs: string[];
  sites: {
    name: string;
    latitude: number;
    longitude: number;
    height_m: number;
    matched: boolean;
    sun: string;
    earth: string;
    overlap: string;
  }[];
};
