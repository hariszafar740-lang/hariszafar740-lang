import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const css = readFileSync(
  new URL('../src/mission-theme.css', import.meta.url),
  'utf8'
);

const token = name => {
  const match = css.match(
    new RegExp(`--${name}:\\s*(#[0-9a-f]{6})`, 'i')
  );
  assert.ok(match, `Missing ${name}`);
  return match[1];
};

const luminance = hex => {
  const values = [1, 3, 5]
    .map(i => parseInt(hex.slice(i, i + 2), 16) / 255)
    .map(x => x <= .04045 ? x / 12.92 : ((x + .055) / 1.055) ** 2.4);

  return .2126 * values[0] + .7152 * values[1] + .0722 * values[2];
};

const ratio = (a, b) => {
  const [low, high] = [luminance(a), luminance(b)].sort((x, y) => x - y);
  return (high + .05) / (low + .05);
};

test('core palette token pairs meet normal-text contrast', () => {
  const pairs = [
    ['mission-text', 'mission-bg'],
    ['mission-muted', 'mission-panel'],
    ['mission-earth', 'mission-panel'],
    ['mission-sun', 'mission-panel'],
    ['mission-action-text', 'mission-action']
  ];

  for (const [foreground, background] of pairs) {
    assert.ok(
      ratio(token(foreground), token(background)) >= 4.5,
      `${foreground} on ${background}`
    );
  }
});
