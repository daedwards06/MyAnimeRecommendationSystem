#!/usr/bin/env python
"""Regenerate the theme files from ``src/app/theme_tokens.py``.

Writes the ``[theme]`` section of ``.streamlit/config.toml`` (other sections untouched) and
``app/styles/tokens.css``. Never edit either by hand; change the tokens and rerun this.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src.app.theme_tokens import render_tokens_css, streamlit_theme

CONFIG_TOML = ROOT / ".streamlit" / "config.toml"
TOKENS_CSS = ROOT / "app" / "styles" / "tokens.css"


def replace_section(text: str, section: str, values: dict[str, str]) -> str:
    """Replace (or append) one ``[section]`` of a flat TOML file, keeping the rest verbatim."""
    body = [f"[{section}]", *(f'{k} = "{v}"' for k, v in values.items())]
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if line.strip() == f"[{section}]"), None)
    if start is None:
        return text.rstrip("\n") + "\n\n" + "\n".join(body) + "\n"
    end = next(
        (i for i in range(start + 1, len(lines)) if lines[i].strip().startswith("[")),
        len(lines),
    )
    while end > start + 1 and not lines[end - 1].strip():
        end -= 1
    return "\n".join([*lines[:start], *body, *lines[end:]]) + "\n"


def main() -> None:
    config = CONFIG_TOML.read_text(encoding="utf-8")
    CONFIG_TOML.write_text(replace_section(config, "theme", streamlit_theme()), encoding="utf-8")
    TOKENS_CSS.parent.mkdir(parents=True, exist_ok=True)
    TOKENS_CSS.write_text(render_tokens_css(), encoding="utf-8")
    print(f"wrote {CONFIG_TOML.relative_to(ROOT)} [theme]")
    print(f"wrote {TOKENS_CSS.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
