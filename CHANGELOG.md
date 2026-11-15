# Changelog

## 2.0.0
- Added a fixed 7×7×7 spatial grid with 343 cells.
- Preserved ordered multi-symbol contents in each occupied cell.
- Added 6-, 18- and 26-connectivity neighbor calculations.
- Added relative-offset spatial pattern definitions and anchor scanning.
- Added exact and contains cell matching modes.
- Added same-cell and adjacency relation constraints scoped to matched cells.
- Added deterministic spatial match results and priority ordering.
- Added JSON serialization and validation for spatial grids.
- Added package exports, specification, tests and GitHub Actions test workflow.
- Kept spatial interpretation based on author-defined rules only.

## 1.9.0
- Added append-only symbolic state memory with SNAPSHOT and TRANSITION events.
- Added timezone-aware ISO-8601 timestamps normalized to UTC.
- Added chronological validation and previous-entry chain integrity.
- Added time-range, event-type and symbol-ID history filters.
- Added state_at lookup and JSON export/import with schema validation.
- Added immutable memory entry metadata and package exports.
- Explicitly documented in-process storage and privacy boundaries.

## 1.8.0
- Added deterministic author-defined emotional pattern recognition.
- Added exact, ordered-subsequence and order-independent contains matching modes.
- Added operator filters, top-level metadata equality conditions and priority ordering.
- Added source component indexes to pattern match results.
- Draft and retired patterns are excluded from recognition.
- Added package exports, specification and unit tests.
- Kept pattern matching separate from psychological inference or diagnosis.

## 1.7.0
- Introduced Emotion Cipher Engine.
- Added author-defined emotion symbols and optional V/A/D/I descriptor vectors.
- Added BASE, BLEND, INTENSIFY, ATTENUATE, CONTRAST, TRANSITION and CONTEXT operators.
- Added validation for symbol status, vector ranges and 7×7×7 coordinates.
- Preserved component identities and order during decoding.
- Separated symbolic interpretation from psychological diagnosis.
