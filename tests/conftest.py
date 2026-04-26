"""Shared pytest fixtures.

Stubs the ``qgis`` package so the plugin's modules can be imported without a
running QGIS instance. Auto-detects whether PyQt6 or PyQt5 is installed and
re-exports its modules under ``qgis.PyQt.*``.

For Qt6, ``QAction``, ``QActionGroup`` and ``QShortcut`` moved from
``QtWidgets`` to ``QtGui``; the real ``qgis.PyQt`` shim re-exports them under
``QtWidgets``, so this stub does the same. Qt5 already has them in
``QtWidgets`` natively, so no re-export is needed there.
"""

import importlib
import sys
import types
from unittest.mock import MagicMock


def _load_pyqt():
    """Import whichever PyQt is installed.

    Returns:
        Tuple ``(qtcore, qtgui, qtwidgets, is_qt6)``. Prefers PyQt6 when both
        are available so the dual-compat smoke test still exercises the Qt6
        path under default CI conditions.
    """
    for major in (6, 5):
        try:
            qtcore = importlib.import_module(f"PyQt{major}.QtCore")
            qtgui = importlib.import_module(f"PyQt{major}.QtGui")
            qtwidgets = importlib.import_module(f"PyQt{major}.QtWidgets")
            return qtcore, qtgui, qtwidgets, major == 6
        except ImportError:
            continue
    raise RuntimeError("Neither PyQt6 nor PyQt5 is installed.")


def _install_qgis_stub() -> None:
    qtcore, qtgui, qtwidgets, is_qt6 = _load_pyqt()

    qgis = types.ModuleType("qgis")
    qgis.__path__ = []
    sys.modules["qgis"] = qgis

    qgis_pyqt = types.ModuleType("qgis.PyQt")
    qgis_pyqt.__path__ = []
    sys.modules["qgis.PyQt"] = qgis_pyqt
    qgis.PyQt = qgis_pyqt

    pyqt_submodules = {
        "QtCore": qtcore,
        "QtGui": qtgui,
        "QtWidgets": qtwidgets,
    }
    for name, real in pyqt_submodules.items():
        alias = types.ModuleType(f"qgis.PyQt.{name}")
        for attr in dir(real):
            if not attr.startswith("_"):
                setattr(alias, attr, getattr(real, attr))
        sys.modules[f"qgis.PyQt.{name}"] = alias
        setattr(qgis_pyqt, name, alias)

    # Qt6 moved QAction/QActionGroup/QShortcut into QtGui; the real
    # qgis.PyQt.QtWidgets shim re-exports them, so mirror that here.
    if is_qt6:
        qtwidgets_alias = sys.modules["qgis.PyQt.QtWidgets"]
        for attr in ("QAction", "QActionGroup", "QShortcut"):
            setattr(qtwidgets_alias, attr, getattr(qtgui, attr))

    for submodule in ("QtSvg", "QtWebEngineWidgets"):
        alias = MagicMock()
        sys.modules[f"qgis.PyQt.{submodule}"] = alias
        setattr(qgis_pyqt, submodule, alias)

    for name in ("core", "gui", "utils"):
        stub = MagicMock()
        stub.__spec__ = None
        sys.modules[f"qgis.{name}"] = stub
        setattr(qgis, name, stub)


_install_qgis_stub()
