# -*- coding: utf-8 -*-
import os

DEBUG_MODE = os.getenv("NGSKINTOOLS_DEBUG", 'false') == 'true'

try:
    from maya import cmds

    BATCH_MODE = cmds.about(batch=True) == 1
except:
    BATCH_MODE = True


def open_ui():
    """
    opens ngSkinTools2 main UI window. if the window is already open, brings that workspace
    window to front.
    """

    from ngSkinTools2.ui import mainwindow

    mainwindow.open()


def reload_package():
    """Reload this package with the reload API available in the current Python."""
    import importlib
    import sys

    reload_module = getattr(importlib, "reload", None)
    if reload_module is None:
        reload_module = reload
    return reload_module(sys.modules[__name__])


def reload_ui():
    """
    Close the current UI, reload Python state/UI modules, and reopen it.

    Intended for Maya Script Editor development workflows where Python source
    changed on disk and restarting Maya would be unnecessarily disruptive.
    The current session is shut down before its module is refreshed so old Qt
    references, callbacks and signal hubs cannot survive the reload.
    """
    if BATCH_MODE:
        raise RuntimeError("ngSkinTools2.reload_ui() requires Maya interactive mode")

    import importlib
    import sys

    from maya import cmds
    from ngSkinTools2 import cleanup
    import ngSkinTools2.api.session as session_module
    from ngSkinTools2.ui.influence_tree_state import sample_influence_reveal_state

    sample_influence_reveal_state.cancel()
    session = session_module.session
    if hasattr(session, "force_end"):
        session.force_end()
    else:
        # Upgrade path from builds that predate Session.force_end(). Keep one
        # sentinel reference while cleanup destroys widgets so their destroyed
        # callbacks cannot recursively end the legacy session.
        session.references.add(-1)
        cleanup.cleanup()
        session.references.clear()
        session.state = None
        session.events = None
        session.context = None
        session.signal_hub = None

    dock_name = "ngSkinTools2_mainWindow"
    if cmds.workspaceControl(dock_name, query=True, exists=True):
        cmds.deleteUI(dock_name)

    invalidate_caches = getattr(importlib, "invalidate_caches", None)
    if invalidate_caches is not None:
        invalidate_caches()

    reload_module = getattr(importlib, "reload", None)
    if reload_module is None:
        reload_module = reload

    loaded_modules = []
    for module_name, module in list(sys.modules.items()):
        if module is None:
            continue
        if (
            module_name == "ngSkinTools2.signal"
            or module_name == "ngSkinTools2.api.influence_names"
            or module_name == "ngSkinTools2.api.session"
            or module_name == "ngSkinTools2.pluginCallbacks"
            or module_name.startswith("ngSkinTools2.operations.")
            or module_name.startswith("ngSkinTools2.ui.")
        ):
            loaded_modules.append((module_name, module))

    def reload_order(item):
        module_name = item[0]
        if module_name == "ngSkinTools2.ui.influence_tree_state":
            return 0, module_name
        if module_name == "ngSkinTools2.signal":
            return 1, module_name
        if module_name == "ngSkinTools2.api.influence_names":
            return 2, module_name
        if module_name == "ngSkinTools2.api.session":
            return 3, module_name
        if module_name.startswith("ngSkinTools2.operations."):
            return 4, module_name
        if module_name == "ngSkinTools2.pluginCallbacks":
            return 6, module_name
        if module_name == "ngSkinTools2.ui.mainwindow":
            return 7, module_name
        return 5, module_name

    for module_name, module in sorted(loaded_modules, key=reload_order):
        try:
            reload_module(module)
        except Exception as err:
            raise RuntimeError("failed reloading {0}: {1}".format(module_name, err))

    open_ui()


def workspace_control_main_window():
    """
    this function is used permanently by Maya's "workspace control", and acts as an alternative top-level entry point to open UI
    """
    from ngSkinTools2.ui import mainwindow
    from ngSkinTools2.ui.paintContextCallbacks import definePaintContextCallbacks

    definePaintContextCallbacks()

    mainwindow.resume_in_workspace_control()
