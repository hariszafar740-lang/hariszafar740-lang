# Accessibility and visual testing

The interface uses text labels and patterns alongside colors for Sun, Earth,
below-clearance and unknown terrain categories. Counts are approximate
midpoint screenings, not operational visibility.

Automated checks cover selected palette token pairs, two rendered
foreground/background combinations, keyboard skip-link behavior, desktop and
mobile browser flows, missing imagery, and a simulated WebGL initialization
failure. Run the frontend tests and browser smoke suite as described in the
project README.

These checks do not cover every control, color pair, screen reader, browser,
dynamic graphic or WCAG criterion. No accessibility certification or
independent human audit is claimed.

Remaining work: manual keyboard and screen-reader testing, color-vision and
contrast review of all states, reduced-motion verification, zoom/reflow
testing, user feedback and independent accessibility review.
