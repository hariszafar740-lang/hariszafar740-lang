# Observations and provenance

The bundled [Diviner subset](diviner/README.md) includes a PDS4 label and 551 historical bolometric brightness temperature bins sourced from a pinned GitHub mirror. It is a small, spatially sparse historical sample, not a live feed. The API checks file hashes and label fields and reports the nearest bin only within 2 km. The sample does not drive the simulation. Read the linked README for product metadata, original archive links, mirror provenance, attribution, and limitations.

`backend/ingest.py` can separately accept a user-prepared CSV with `timestamp,quantity,value,unit,source_url` and write `observations.csv`. It checks formatting and NASA/PDS-related URL domains, but it does not verify provenance or parse PDS labels. A source URL alone does not prove an observation is authentic. The normalized CSV is not consumed by the simulation or Diviner endpoint. Do not import rows until their product label, units, selection and provenance have been reviewed.
