// Zoom around the controls target without crossing the configured limits.
export function zoomCamera(camera, controls, factor) {
  const offset = camera.position.clone().sub(controls.target);
  const distance = offset.length();

  if (
    !Number.isFinite(distance) || distance <= 0 ||
    !Number.isFinite(factor) || factor <= 0
  ) return;

  const next = Math.max(
    controls.minDistance,
    Math.min(controls.maxDistance, distance * factor)
  );

  camera.position.copy(controls.target).add(
    offset.multiplyScalar(next / distance)
  );
  controls.update();
}
