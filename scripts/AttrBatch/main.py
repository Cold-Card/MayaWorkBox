import maya.cmds as cmds

maya_version = cmds.about(version=True)
try:
    if int(maya_version) >= 2025:
        from PySide6 import QtCore
    else:
        from PySide2 import QtCore
except ValueError:
    from PySide2 import QtCore

import os

from AttrBatch.UI.data_exchange import DataExchange
from AttrBatch.UI.UI_metrics import UI_metrics
from AttrBatch.UI.UI_utilities import UI_Utilities

def create_gui(root_path, settings_path):

    # to support UI scaling running this before importing main window
    base_scale = UI_Utilities.find_ui_scale()
    DataExchange.set_value("root_path", root_path)
    DataExchange.set_value("settings_path", settings_path)
    DataExchange.set_value("base_scale", base_scale)

    if UI_metrics.pro_version:
        from AttrBatch.UI.main_window_pro import AttrBatchProUI
    else:
        from AttrBatch.UI.main_window import AttrBatchUI

    MainWindowUI = AttrBatchProUI if UI_metrics.pro_version else AttrBatchUI

    # cleanup old window
    if cmds.window(UI_metrics.main_widget_window_id, exists=1):
        cmds.deleteUI(UI_metrics.main_widget_window_id)
    if cmds.windowPref(UI_metrics.main_widget_window_id, exists=1):
        cmds.windowPref(UI_metrics.main_widget_window_id, remove=1)

    # launch 
    global AttrBatchDialog
    AttrBatchDialog = MainWindowUI(scale=base_scale, root_path=root_path, settings_path=settings_path)
    AttrBatchDialog.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    AttrBatchDialog.closeEvent = lambda event: AttrBatchDialog.deleteLater()
    AttrBatchDialog.show()


def main(settings_path=""):
    root_path = os.path.dirname(__file__)
    create_gui(root_path, settings_path)