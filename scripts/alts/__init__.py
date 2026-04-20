"""Alternate itinerary builders (A / B / D).

Each module here defines a ``build()`` entrypoint that calls
``trip_core.build_payload`` and writes a dedicated ``trip_data_alt_<x>.json``.
The HTML/GPX renderer (``scripts/build_deliverables.py``) iterates over all
alt JSONs to produce per-alternate pages.
"""
