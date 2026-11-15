// Comparison of recorded inputs and midpoint-bin outputs; no causal inference.
const delta = (a, b) => {
  const d = a - b;
  return `${d > 0 ? '+' : ''}${d.toFixed(2)} h`;
};

export function describeChanges(base, current) {
  const inputs = [];

  const add = (label, a, b) => {
    if (a !== b) inputs.push(`${label}: ${a} → ${b}`);
  };

  add('Start (UTC)', base.start, current.start);
  add('End (UTC)', base.end, current.end);
  add(
    'Duration (hours)',
    (Date.parse(base.end) - Date.parse(base.start)) / 3600000,
    (Date.parse(current.end) - Date.parse(current.start)) / 3600000
  );
  add('Bin size (minutes)', base.step_minutes, current.step_minutes);
  add('Sun clearance (degrees)', base.sun_clearance_deg, current.sun_clearance_deg);
  add('Earth clearance (degrees)', base.earth_clearance_deg, current.earth_clearance_deg);
  add('Model version', base.model_version, current.model_version);
  add('Dataset kind', base.dataset_kind, current.dataset_kind);
  add('Dataset SHA-256', base.dataset_sha256, current.dataset_sha256);

  const key = s => `${s.latitude}|${s.longitude}|${s.height_m}`;
  const before = base.sites.map(key).sort();
  const after = current.sites.map(key).sort();

  if (JSON.stringify(before) !== JSON.stringify(after)) {
    inputs.push(
      'Site coordinates, observer heights, or number of sites changed; ' +
      'only unique coordinate matches are compared.'
    );
  }

  const sites = current.sites.map(site => {
    const matches = base.sites.filter(b => key(b) === key(site));
    const currentMatches = current.sites.filter(b => key(b) === key(site));
    const match = matches.length === 1 && currentMatches.length === 1
      ? matches[0]
      : null;

    return {
      name: site.name,
      latitude: site.latitude,
      longitude: site.longitude,
      height_m: site.height_m,
      matched: !!match,
      sun: match ? delta(site.sun_hours, match.sun_hours) : '',
      earth: match ? delta(site.earth_hours, match.earth_hours) : '',
      overlap: match ? delta(site.overlap_hours, match.overlap_hours) : ''
    };
  });

  return {inputs, sites};
}
