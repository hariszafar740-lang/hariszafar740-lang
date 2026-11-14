# LRO Diviner observational subset

`diviner_label.xml` is the original PDS4 label for product
`urn:nasa:pds:lro_diviner_derived1:data_derived_pcp:pcp_avg_tbol_pols_ls030_slon01_240`.
`diviner_subset.tab` contains the original header and 551 selected, verbatim
rows, **not** the 3,176,166 rows described by the full-product label. This is
NASA LRO Diviner polar cumulative-product bolometric brightness temperature,
binned at 240 m and compiled from nadir observations over 2009–2020, for
season Ls 0–60 degrees and subsolar longitude 0–15 degrees. See the label for
the authoritative metadata. Historical averages are neither real-time values
nor necessarily representative of the current simulated phase.

- Original NASA PDS [label](https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_pcp/seasonal/slon/pols/pcp_avg_tbol_pols_ls030_slon01_240.xml) and [full table](https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_pcp/seasonal/slon/pols/pcp_avg_tbol_pols_ls030_slon01_240.tab).
- Retrieved via [GitHub mirror, pinned commit](https://github.com/julianascencio/orbital-pv/tree/7c2b1a64f7d43b9662b022ac3b88351228bbd3cd/examples/lunar/_data). Upstream [provenance](https://github.com/julianascencio/orbital-pv/blob/7c2b1a64f7d43b9662b022ac3b88351228bbd3cd/examples/lunar/_data/provenance.json) describes selection within 2 km of three sites and provides hashes. NASA PDS was not directly reachable in this environment, so the subset's claimed derivation has not been independently compared to the full NASA table.
- Subset SHA-256: `3549df564f412a0d573383d7fe17e809f383cf8455a2a13de9a83e05aa431537`; label SHA-256: `c434aa4916cf70917a09ecbed4c6bd44537ff343687c6c9c056ede843a4064e8`. Checksums agree with the mirror's provenance.
- Credit: NASA PDS / LRO Diviner / Jean-Pierre Williams and UCLA. Original data retains its own terms; this project's license does not relicense NASA data or imply NASA endorsement. The mirror's repository license applies to its software, not separately identified third-party data.

The API parses and checks the PDS label and pinned hashes, validates records,
and performs a spherical nearest-neighbor lookup with a 2 km maximum distance.
It refuses to return a value outside that coverage. A nearest bin is not
interpolation and is not necessarily representative of a site, particularly
near shadow boundaries. The observation is displayed separately from the
model and does not calibrate or drive it. LADEE, global Diviner coverage and
matched-condition validation remain future work.
