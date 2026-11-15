import type {PerspectiveCamera} from 'three';
import type {OrbitControls} from 'three/examples/jsm/controls/OrbitControls.js';

export function zoomCamera(
  camera: PerspectiveCamera,
  controls: OrbitControls,
  factor: number
): void;
