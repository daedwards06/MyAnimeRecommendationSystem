"""The app's one stylesheet entry point: tokens.css, base.css and components.css, injected once per run."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx

STYLES_DIR = Path(__file__).resolve().parent
STYLESHEETS: tuple[str, ...] = ("tokens.css", "base.css", "components.css")


@lru_cache(maxsize=1)
def stylesheet() -> str:
    """The three files concatenated, with every ``@import`` hoisted first so browsers honour it."""
    text = "\n".join((STYLES_DIR / name).read_text(encoding="utf-8") for name in STYLESHEETS)
    lines = text.splitlines()
    imports = [line for line in lines if line.lstrip().startswith("@import")]
    rest = [line for line in lines if not line.lstrip().startswith("@import")]
    return "\n".join([*imports, *rest]) + "\n"


def inject_styles() -> bool:
    """Emit the stylesheet unless this run already has it; returns whether it was emitted.

    Streamlit drops elements a rerun does not re-emit, so this must run every run. The run is
    identified by the context's ``cursors`` dict, which ``ScriptRunContext.reset`` replaces at
    the start of each run; holding a reference to it means a later run can never match it.
    """
    ctx = get_script_run_ctx(suppress_warning=True)
    run_marker = getattr(ctx, "cursors", None)
    if run_marker is not None and getattr(ctx, "_mars_styles_run", None) is run_marker:
        return False
    st.markdown(f"<style>\n{stylesheet()}</style>", unsafe_allow_html=True)
    if run_marker is not None:
        ctx._mars_styles_run = run_marker
    return True


__all__ = ["STYLESHEETS", "inject_styles", "stylesheet"]
