# Lunar globe imagery provenance

The Exosphere Lab globe uses the 2048 × 1024 JPEG `lroc_color_2k.jpg`
from NASA Scientific Visualization Studio's
[CGI Moon Kit](https://svs.gsfc.nasa.gov/4720/), visualization by Ernie
Wright, using LRO camera and laser altimeter data.

[Original image](https://svs.gsfc.nasa.gov/vis/a000000/a004700/a004720/lroc_color_2k.jpg).

The image is bundled unchanged. SHA-256:
`f7130a1822681fa7512d7dcfd40db8c10b9ba4f06777910348698260ed7a2170`.

NASA states that the image is optimized for aesthetics, not science; polar
areas include lower-resolution LOLA albedo and some gaps are inpainted. The
globe uses this image for visual context, not as elevation, a terrain horizon,
or evidence of local surface conditions. Lighting is illustrative. NASA does
not endorse this project. See
[NASA media usage guidelines](https://www.nasa.gov/nasa-brand-center/images-and-media/).

The image is bundled for offline use after installation. If it cannot load,
a visibly labeled procedural fallback is shown. The texture is flipped
horizontally to match the application's east-positive longitude convention.
This mapping is an implementation assumption and is not independently
verified against lunar landmarks; do not use the globe for precise geographic
selection or mission decisions. Coordinate and landmark validation is planned
separately.

Display lighting uses a visual fill light to preserve surface detail, and rings and particles are subdued schematic effects. Brightness and shadows do not represent measured or predicted surface illumination.

Globe zoom buttons and reset affect only the camera. Clicking the globe changes the selected coordinates; users may also enter coordinates in the inspector. Imagery alignment has not been independently checked against lunar landmarks.

The Exosphere Lab and Site Navigator can pass the selected latitude and longitude between views. A new navigator comparison starts with default dates, thresholds and observer height; it does not transfer terrain results or imply matching physical models.

If WebGL initialization fails, the app shows a text fallback; coordinate entry in the site inspector remains available. Browser smoke tests simulate a failed WebGL context, but do not establish full accessibility compliance.
