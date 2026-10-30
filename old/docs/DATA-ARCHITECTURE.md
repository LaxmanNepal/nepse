# NEPSE Pulse Data Architecture — Phase 1

## Goal

Make every market snapshot traceable, validated, and explicit about freshness before it reaches the static web application.

## Pipeline

`source -> fetch -> normalize -> validate -> freshness/health -> cache -> web UI`

## Canonical snapshot

`data/live.json` is the application snapshot. It must include:

- `updatedAt`: UTC time when this repository snapshot was generated
- `source`: source identity
- `sourceUpdatedAt`: source-provided freshness timestamp when available
- `market`: source market-status payload
- `index`: canonical NEPSE index row
- `summary`: market summary payload
- `stocks`: normalized security rows

Unknown values remain `null`; they must not be replaced with zero.

## Freshness

The pipeline records both repository generation time and source update time. Consumers must use the source timestamp when it is available and must visibly distinguish fresh, aging, stale, and unavailable data.

## Validation

The validator checks:

- snapshot structure
- non-empty stock collection
- unique normalized symbols
- numeric/non-negative price and market fields
- OHLC consistency where all values are available
- valid percentage/change values
- valid timestamps
- required metadata

Validation failure must stop publication. A source failure must never be represented as an apparently valid zero-filled dataset.

## Current deployment model

The site is static-first and GitHub Actions materializes `data/` snapshots. This is periodic/static publishing, not a true low-latency market-data feed. Phase 1 therefore avoids claiming real-time data unless the source and delivery path support that latency.

## Trading calendar

Collectors must prefer the source's market status. A calendar heuristic is only a fallback. NEPSE normally trades Sunday–Thursday, 11:00–15:00 Nepal time, but holidays and exchange status can override that schedule.
