"""
Maxar Open Data Plugin Dialogs

This module contains the dialog and dock widget classes for the Maxar Open Data plugin.
"""

from .maxar_dock import MaxarDockWidget
from .settings_dock import SettingsDockWidget
from .update_checker import UpdateCheckerDialog

__all__ = [
    "MaxarDockWidget",
    "SettingsDockWidget",
    "UpdateCheckerDialog",
]
