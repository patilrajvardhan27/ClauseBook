"""Shared Python core: ontology models, placement engine, diff, config, db session.

Imported by both the API (for playbook previews) and the worker (for full
review runs), so the placement logic exists in exactly one place.
"""
