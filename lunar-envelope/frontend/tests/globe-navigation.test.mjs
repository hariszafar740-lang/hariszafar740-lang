import test from 'node:test';
import assert from 'node:assert/strict';
import {PerspectiveCamera, Vector3, SphereGeometry} from 'three';
import {zoomCamera} from '../src/globe-navigation.mjs';

test('zoom respects target and distance limits', () => {
  const camera = new PerspectiveCamera();
  camera.position.set(3, 0, 0);

  let updates = 0;
  const controls = {
    target: new Vector3(1, 0, 0),
    minDistance: 1,
    maxDistance: 4,
    update() { updates++; }
  };

  zoomCamera(camera, controls, .1);
  assert.equal(camera.position.distanceTo(controls.target), 1);

  zoomCamera(camera, controls, 100);
  assert.equal(camera.position.distanceTo(controls.target), 4);

  assert.equal(updates, 2);
  zoomCamera(camera, controls, NaN);
  assert.equal(updates, 2);
});

test('selected sphere UVs match east-positive texture convention', () => {
  const geometry = new SphereGeometry(2, 96, 64);
  const positions = geometry.getAttribute('position');
  const uvs = geometry.getAttribute('uv');

  for (const lat of [-45, 0, 45]) {
    for (const lon of [-90, 0, 90]) {
      const a = lat * Math.PI / 180;
      const b = lon * Math.PI / 180;
      const target = new Vector3(
        2 * Math.cos(a) * Math.cos(b),
        2 * Math.sin(a),
        2 * Math.cos(a) * Math.sin(b)
      );

      let index = -1;
      let closest = Infinity;

      for (let i = 0; i < positions.count; i++) {
        const distance = new Vector3()
          .fromBufferAttribute(positions, i)
          .distanceTo(target);

        if (distance < closest) {
          closest = distance;
          index = i;
        }
      }

      assert.ok(closest < 1e-5);

      const textureU = ((1 - uvs.getX(index)) % 1 + 1) % 1;
      assert.ok(Math.abs(textureU - (.5 + lon / 360)) < 1e-5);
      assert.ok(Math.abs(uvs.getY(index) - (.5 + lat / 180)) < 1e-5);
    }
  }

  geometry.dispose();
});
