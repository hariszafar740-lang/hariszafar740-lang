import test from 'node:test';
import assert from 'node:assert/strict';
import {describeChanges} from '../src/comparison.mjs';

const site = {
  name: 'A', latitude: -85, longitude: 0, height_m: 0,
  sun_hours: 10, earth_hours: 8, overlap_hours: 4
};

const base = {
  start: '2026-11-14T12:00:00Z',
  end: '2026-11-21T12:00:00Z',
  step_minutes: 60,
  sun_clearance_deg: 0,
  earth_clearance_deg: 0,
  model_version: 'v1',
  dataset_kind: 'extended',
  dataset_sha256: 'abc',
  sites: [site]
};

test('unchanged inputs and outputs', () => {
  const r = describeChanges(base, base);
  assert.deepEqual(r.inputs, []);
  assert.equal(r.sites[0].overlap, '0.00 h');
});

test('describes changed settings and three signed metrics', () => {
  const current = {
    ...base,
    end: '2026-11-17T12:00:00Z',
    step_minutes: 15,
    sun_clearance_deg: 1,
    dataset_sha256: 'def',
    sites: [{...site, sun_hours: 12, earth_hours: 7, overlap_hours: 4.5}]
  };

  const r = describeChanges(base, current);
  assert.ok(r.inputs.some(x => x.startsWith('Duration (hours)')));
  assert.ok(r.inputs.some(x => x.startsWith('Dataset SHA-256')));
  assert.deepEqual(
    [r.sites[0].sun, r.sites[0].earth, r.sites[0].overlap],
    ['+2.00 h', '-1.00 h', '+0.50 h']
  );
});

test('changed coordinates do not produce invented deltas', () => {
  const r = describeChanges(base, {
    ...base,
    sites: [{...site, latitude: -86}]
  });

  assert.equal(r.sites[0].matched, false);
  assert.ok(r.inputs.some(x => x.startsWith('Site coordinates')));
});

test('duplicate coordinates are not uniquely matched', () => {
  const r1 = describeChanges({...base, sites: [site, site]}, base);
  const r2 = describeChanges(base, {...base, sites: [site, site]});
  assert.equal(r1.sites[0].matched, false);
  assert.equal(r2.sites[0].matched, false);
});
