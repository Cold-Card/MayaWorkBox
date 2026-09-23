# -*- coding: utf-8 -*-
"""
Maya 2022 / Maya 2026 PySide2 compatibility layer.

IMPORTANT
---------
Do NOT name this file "PySide2.py".

Recommended filename:
    maya_pyside2_compat.py

Reason:
    A file named PySide2.py inside Maya's scripts path can shadow Maya's
    real PySide2 package and break Maya 2022 during startup.

Usage:
    import maya_pyside2_compat as compat
    compat.install()

Only Maya 2026 needs the compatibility layer. Maya 2022 is left completely
untouched.

This module is intentionally opt-in: importing this module does NOT modify
PySide2/PySide6/sys.modules. The compatibility layer is installed only when
install() is explicitly called.
"""

from __future__ import print_function

import sys
import importlib
from types import ModuleType


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SUPPORTED_MAYA_VERSION = "2026"


# ---------------------------------------------------------------------------
# Maya version
# ---------------------------------------------------------------------------

def get_maya_version():
    """Return Maya major version as a string, or None outside Maya."""
    try:
        import maya.cmds as cmds
        return str(cmds.about(version=True)).split()[0]
    except Exception:
        return None


def is_maya_2026():
    return get_maya_version() == SUPPORTED_MAYA_VERSION


def is_maya_2022():
    return get_maya_version() == "2022"


# ---------------------------------------------------------------------------
# Installation state
# ---------------------------------------------------------------------------

_INSTALLED = False


def is_installed():
    return _INSTALLED


# ---------------------------------------------------------------------------
# Module proxy helpers
# ---------------------------------------------------------------------------

def _ensure_pyside2_package():
    """
    Create the PySide2 compatibility package only when installation is
    explicitly requested.

    Never execute this automatically at import time.
    """
    existing = sys.modules.get("PySide2")

    if existing is not None:
        return existing

    package = ModuleType("PySide2")
    package.__path__ = []
    package.__package__ = "PySide2"

    sys.modules["PySide2"] = package
    return package


def _map_module(package, name, source_module):
    """Map PySide2.<name> to a PySide6 module."""
    target_name = "PySide2." + name

    sys.modules[target_name] = source_module
    setattr(package, name, source_module)


# ---------------------------------------------------------------------------
# Qt compatibility patches
# ---------------------------------------------------------------------------

def _patch_moved_classes(QtGui, QtWidgets):
    """
    Qt6 moved several classes from QtWidgets to QtGui.

    Put the commonly used Qt5 locations back on QtWidgets.
    """
    moved_classes = (
        "QAction",
        "QActionGroup",
        "QShortcut",
        "QUndoCommand",
        "QUndoStack",
        "QUndoGroup",
        "QUndoView",
        "QFileSystemModel",
    )

    for name in moved_classes:
        if hasattr(QtGui, name):
            try:
                setattr(QtWidgets, name, getattr(QtGui, name))
            except Exception:
                pass


def _patch_exec():
    """Restore the PySide2-style exec_() API where possible."""
    try:
        from PySide6 import QtCore, QtWidgets
    except ImportError:
        return

    classes = (
        QtWidgets.QDialog,
        QtWidgets.QApplication,
        QtWidgets.QMenu,
        QtCore.QCoreApplication,
        QtCore.QThread,
        QtCore.QEventLoop,
    )

    for cls in classes:
        try:
            if hasattr(cls, "exec") and not hasattr(cls, "exec_"):
                setattr(cls, "exec_", cls.exec)
        except Exception:
            pass


def _patch_common_enums():
    """
    Restore common Qt5-style enum access such as:

        Qt.AlignLeft
        Qt.AlignCenter
        Qt.Horizontal
        Qt.Vertical

    Qt6 normally exposes these through scoped enum classes.
    """
    try:
        from PySide6 import QtCore, QtWidgets
    except ImportError:
        return

    def promote(source, names):
        for name in names:
            try:
                if not hasattr(source, name):
                    enum_owner = None

                    # Search the most common scoped enum containers.
                    for owner_name in (
                        "AlignmentFlag",
                        "Orientation",
                        "KeyboardModifier",
                        "MouseButton",
                        "WindowType",
                        "FocusPolicy",
                        "ContextMenuPolicy",
                        "ItemDataRole",
                        "ItemFlag",
                        "SortOrder",
                        "DockWidgetArea",
                        "ToolBarArea",
                        "WindowState",
                        "WindowModality",
                    ):
                        owner = getattr(source, owner_name, None)
                        if owner is not None and hasattr(owner, name):
                            enum_owner = owner
                            break

                    if enum_owner is not None:
                        setattr(source, name, getattr(enum_owner, name))
            except Exception:
                pass

    qt_names = (
        "AlignLeft",
        "AlignRight",
        "AlignHCenter",
        "AlignJustify",
        "AlignTop",
        "AlignBottom",
        "AlignVCenter",
        "AlignCenter",
        "Horizontal",
        "Vertical",
        "LeftButton",
        "RightButton",
        "MiddleButton",
        "NoButton",
        "ShiftModifier",
        "ControlModifier",
        "AltModifier",
        "MetaModifier",
        "Window",
        "Dialog",
        "Tool",
        "FramelessWindowHint",
        "WindowStaysOnTopHint",
        "WindowModal",
        "NonModal",
    )

    promote(QtCore.Qt, qt_names)

    frame_names = (
        "NoFrame",
        "Box",
        "Panel",
        "StyledPanel",
        "HLine",
        "VLine",
        "Sunken",
        "Raised",
    )

    try:
        promote(QtWidgets.QFrame, frame_names)
    except Exception:
        pass


def _patch_shiboken2():
    """
    Map shiboken2 to shiboken6.

    This is deliberately performed only during explicit installation.
    """
    try:
        import shiboken6

        sys.modules["shiboken2"] = shiboken6
        return shiboken6
    except ImportError:
        return None


# ---------------------------------------------------------------------------
# Installation
# ---------------------------------------------------------------------------

def install(force=False):
    """
    Install the compatibility layer.

    Default behavior:
        - Maya 2022: do nothing.
        - Maya 2026: install PySide2 -> PySide6 compatibility.
        - Other Maya versions: do nothing.
        - Outside Maya: do nothing.

    force=True can be used for testing outside the normal version guard.
    """
    global _INSTALLED

    if _INSTALLED:
        return True

    version = get_maya_version()

    if not force and version != SUPPORTED_MAYA_VERSION:
        return False

    try:
        import PySide6
    except ImportError:
        print(
            "PySide2 compatibility: PySide6 is not available; "
            "compatibility layer was not installed."
        )
        return False

    # Import all source modules before changing sys.modules.
    import PySide6.QtCore as QtCore
    import PySide6.QtGui as QtGui
    import PySide6.QtWidgets as QtWidgets
    import PySide6.QtUiTools as QtUiTools

    optional_modules = (
        "QtNetwork",
        "QtSvg",
        "QtOpenGL",
        "QtPrintSupport",
        "QtSql",
        "QtTest",
        "QtXml",
    )

    package = _ensure_pyside2_package()

    # Core modules used by most Maya tools.
    _map_module(package, "QtCore", QtCore)
    _map_module(package, "QtGui", QtGui)
    _map_module(package, "QtWidgets", QtWidgets)
    _map_module(package, "QtUiTools", QtUiTools)

    for name in optional_modules:
        try:
            module = importlib.import_module("PySide6." + name)
            _map_module(package, name, module)
        except ImportError:
            pass

    # Apply API compatibility patches.
    _patch_moved_classes(QtGui, QtWidgets)
    _patch_exec()
    _patch_common_enums()
    _patch_shiboken2()

    # Make package attributes available for:
    #     from PySide2 import QtCore
    package.QtCore = QtCore
    package.QtGui = QtGui
    package.QtWidgets = QtWidgets
    package.QtUiTools = QtUiTools

    _INSTALLED = True

    print(
        "--- Maya {} PySide2 compatibility layer installed "
        "(PySide6 backend) ---".format(version or "2026")
    )

    return True


def uninstall():
    """
    Remove mappings created by this compatibility layer.

    This is primarily useful for development/testing.

    NOTE:
    Do not call this while live Qt widgets are using the mapped modules.
    """
    global _INSTALLED

    if not _INSTALLED:
        return

    module_names = (
        "PySide2.QtCore",
        "PySide2.QtGui",
        "PySide2.QtWidgets",
        "PySide2.QtUiTools",
        "PySide2.QtNetwork",
        "PySide2.QtSvg",
        "PySide2.QtOpenGL",
        "PySide2.QtPrintSupport",
        "PySide2.QtSql",
        "PySide2.QtTest",
        "PySide2.QtXml",
        "shiboken2",
    )

    for name in module_names:
        sys.modules.pop(name, None)

    # Remove our synthetic package only if it is the object we created.
    package = sys.modules.get("PySide2")
    if package is not None and getattr(package, "__package__", None) == "PySide2":
        sys.modules.pop("PySide2", None)

    _INSTALLED = False


# ---------------------------------------------------------------------------
# Optional convenience API
# ---------------------------------------------------------------------------

def ensure():
    """
    Safe convenience entry point.

    Maya 2022:
        returns False and does absolutely nothing.

    Maya 2026:
        installs the compatibility layer and returns True.
    """
    return install()


# ---------------------------------------------------------------------------
# IMPORTANT: no automatic execution here.
#
# Do NOT write:
#     install()
#
# This module must be safe to import from Maya 2022.
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Running the file directly is allowed, but still respects the version
    # guard unless force=True is explicitly used from Python.
    install()
