"""Simple smoke test for Streamlit app imports.

Run:
    python scripts/smoke_app_test.py

Expected:
    Prints 'APP_IMPORT_OK' if import path resolves without exceptions.
"""

from __future__ import annotations

def main() -> None:
    try:
        __import__("app.main")
    except Exception as e:  # noqa: BLE001
        print("APP_IMPORT_FAIL", type(e).__name__, e)
        raise
    else:
        print("APP_IMPORT_OK")


if __name__ == "__main__":  # pragma: no cover
    main()
