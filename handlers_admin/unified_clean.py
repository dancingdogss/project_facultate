"""Compatibility shim for older imports.

This module now simply re-exports the canonical unified interface implementation so
that any legacy references to ``handlers_admin.unified_clean`` continue to work.
"""

from handlers_admin.unified_interface import *  # noqa: F401,F403