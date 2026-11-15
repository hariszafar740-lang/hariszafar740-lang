import test from 'node:test';
import assert from 'node:assert/strict';
import {buildExport} from '../src/export-report.mjs';

const site = {
  name: 'A',
  latitude: -85,
  longitude: 0,
  height_m: 0,
  sun_hours: 10,
  earth_hours: 8,
  overlap_hours: 4
};

const plan = {
  start: '2026-11-14T12:00:00Z',
  end: '2026-11-21T12:00:00Z',
  step_minutes: 60,
  sun_clearance_deg: 0,
  earth_clearance_deg: 0,
  model_version: 'v1',
  dataset_kind: 'extended',
  dataset_sha256: 'abc',
  assumptions: {frame: 'example'},
  limits: 'Example limits',
  sites: [site]
};

test('report preserves snapshot and labels missing revision', () => {
  const report = buildExport(plan, null, '2026-11-15T00:00:00.000Z');
  const result = JSON.parse(JSON.stringify(report));

  assert.equal(result.schema, 'lunaris-site-comparison-v1');
  assert.equal(result.exported_at_utc, '2026-11-15T00:00:00.000Z');
  assert.deepEqual(result.current, plan);
  assert.equal(result.baseline, null);
  assert.equal(result.change_summary, null);
  assert.equal(result.manifest.code_revision, null);
  assert.match(result.manifest.terrain, /separate/);
});

test('baseline and changes survive JSON serialization', () => {
  const current = {
    ...plan,
    sites: [{...site, overlap_hours: 5}]
  };

  const result = JSON.parse(
    JSON.stringify(buildExport(current, plan))
  );

  assert.deepEqual(result.baseline, plan);
  assert.equal(result.change_summary.sites[0].overlap, '+1.00 h');
  assert.match(result.notice, /not flight qualified/);
});
