"""Smoke test to ensure Streamlit app entrypoint imports cleanly."""

from __future__ import annotations

import os


def test_app_import():
    # Enable lightweight mode to bypass heavy artifact loading in tests.
    os.environ["APP_IMPORT_LIGHT"] = "1"
    __import__("app.main")
