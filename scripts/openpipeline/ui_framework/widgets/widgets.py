# -*- coding: utf-8 -*-

try:
    from PySide6 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui

class Widgets(object):
    def __init__(self):
        self.button_bgc = (
            'background-color:#C5C5C5;'
        )

    def maya_main_window(self):
        try:
            import maya.OpenMayaUI as omui
            try:
                from shiboken6 import wrapInstance
            except Exception:
                try:
                    from shiboken2 import wrapInstance
                except Exception:
                    wrapInstance = None

            if wrapInstance is None:
                return None

            ptr = omui.MQtUtil.mainWindow()
            if ptr is None:
                return None

            return wrapInstance(int(ptr), QtWidgets.QWidget)
        except Exception:
            return None

    def separator(self, parent, H=True):
        try:
            frame = QtWidgets.QFrame()
            frame.setFrameShape(QtWidgets.QFrame.HLine if H else QtWidgets.QFrame.VLine)
            frame.setFrameShadow(QtWidgets.QFrame.Sunken)
            frame.setLineWidth(1)
            if hasattr(parent, 'addWidget'):
                parent.addWidget(frame)
            return frame
        except Exception:
            return None

    def create_copyrightText(self, parent_layout, timestamp):
        self.separator(parent_layout, True)
        label = QtWidgets.QLabel('OpenPipeline ({})   Wang Ruilong (rigger)'.format(timestamp))
        label.setStyleSheet('color:#8c8c8c; font: bold 8px;')
        parent_layout.addWidget(label)
        return label


class PyouPersistentWindow(QtWidgets.QWidget):
    def __init__(self, app_name, window_name, parent=None):
        super(PyouPersistentWindow, self).__init__(parent)
        self.app_name = app_name
        self.window_name = window_name

    def _var_name(self, key):
        return "{}_{}".format(self.app_name, key)

    def loadWindowSettings(self):
        try:
            import maya.cmds as cmds

            # 恢复窗口位置和大小
            geo_var = self._var_name("geometry")
            if cmds.optionVar(exists=geo_var):
                data = str(cmds.optionVar(q=geo_var))
                ba = QtCore.QByteArray(data.encode('ascii'))
                self.restoreGeometry(QtCore.QByteArray.fromBase64(ba))
        except Exception as e:
            import maya.cmds as cmds
            cmds.warning("loadWindowSettings failed: {}".format(e))

    def saveWindowSettings(self):
        try:
            import maya.cmds as cmds

            # 保存窗口位置和大小
            geo = self.saveGeometry().toBase64().data()
            if isinstance(geo, bytes):
                geo = geo.decode('ascii')
            cmds.optionVar(sv=(self._var_name("geometry"), geo))
        except Exception as e:
            import maya.cmds as cmds
            cmds.warning("saveWindowSettings failed: {}".format(e))


__all__ = ['Widgets', 'PyouPersistentWindow']
