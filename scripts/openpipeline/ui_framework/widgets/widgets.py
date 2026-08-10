# -*- coding: utf-8 -*-

from openpipeline.ui_framework.core.qtCompat import QtCore, QtGui, QtWidgets

class Widgets(object):
    def __init__(self):
        self.button_bgc = (
            'background-color:#C5C5C5;'
        )

    def maya_main_window(self):
        try:
            import maya.OpenMayaUI as omui
            try:
                from shiboken2 import wrapInstance
            except Exception:
                try:
                    from shiboken import wrapInstance
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

    def separator(self, parent, vertical=False):
        try:
            frame = QtWidgets.QFrame()
            frame.setFrameShape(QtWidgets.QFrame.HLine if vertical else QtWidgets.QFrame.VLine)
            frame.setFrameShadow(QtWidgets.QFrame.Sunken)
            frame.setLineWidth(1)
            if hasattr(parent, 'addWidget'):
                parent.addWidget(frame)
            return frame
        except Exception:
            return None

    def create_text(self, text=''):
        label = QtWidgets.QLabel(text)
        label.setStyleSheet('color:#5285A6; font: bold 12px;')
        return label

    def create_copyrightText(self, parent_layout, timestamp):
        self.separator(parent_layout, True)
        label = QtWidgets.QLabel('OpenPipeline ({})   Wang Ruilong (rigger)'.format(timestamp))
        label.setStyleSheet('color:#8c8c8c; font: bold 10px;')
        parent_layout.addWidget(label)
        return label

    def apply_openpipeline_style(self, widget):
        """
        OpenPipeline 独立Qt样式
        只影响当前插件窗口，不影响Maya
        """

        style = """
        /* ── 全局基础 ── */
        QWidget {
            font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
            background-color: #353535;
        }

        /* ── 分组框 ── */
        QGroupBox {
            background-color: #454545;
            border: 1px solid #4E4E4E;
            border-radius: 6px;
            margin-top: 8px;
            padding-top: 6px;
            padding-bottom: 3px;
            padding-left: 3px;
            padding-right: 3px;
            font-weight: bold;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 6px;
            border-radius: 3px;
            padding: 0px 3px;
            color: #5285A6;
            background-color: #454545;
        }

        /* ── 标签 ── */
        QLabel {
            color: #eeeeee;
            background: transparent;
            font-weight: bold;
            font-size: 12px;
        }

        /* ── 按钮 ── */
        QPushButton {
            background-color: #5A5F68;
            color: #eeeeee;
            border-radius: 6px;
            padding: 4px 4px;
            font-weight: bold;
            font-size: 12px;
        }
        QPushButton:hover {
            background-color: #6C7380;
        }
        QPushButton:pressed {
            background-color: #33363B;
        }
        QPushButton:disabled {
            background-color: #333333;
            color: #666666;
        }

        /* 白色按钮 */
        QPushButton[white="true"] {
            color: #000000;
            background-color: #ADADAD;
            border-radius: 6px;
            padding: 4px 4px;
            font-weight: bold;
            font-size: 12px;            
        }
        QPushButton[white="true"]:hover {
            background-color: #DFDFDF;
        }
        QPushButton[white="true"]:disabled {
            background-color: #333333;
            color: #666666;
        }

        /* 绿色按钮 */
        QPushButton[green="true"] {
            color: #2F7A00;
            background-color: #ADADAD;
            border-radius: 6px;
            padding: 4px 4px;
            font-weight: bold;
            font-size: 12px;
        }
        QPushButton[green="true"]:hover {
            background-color: #DFDFDF;
        }
        QPushButton[green="true"]:disabled {
            background-color: #333333;
            color: #666666;
        }

        /* 红色按钮 */
        QPushButton[red="true"] {
            color: #FF0000;
            background-color: #ADADAD;
        }
        QPushButton[red="true"]:hover {
            background-color: #DFDFDF;
        }
        QPushButton[red="true"]:disabled {
            background-color: #333333;
            color: #666666;
        }

        /* ── 下拉框 ── */
        QComboBox {
            background-color: #5D5D5D;
            
        }

        /* ── 输入框 / 搜索框 ── */
        QLineEdit, QTextEdit {
            background-color: #272727;
            border: 1px solid #272727;
            border-radius: 3px;
            padding: 4px;
        }
        QLineEdit:focus, QTextEdit:focus {
            border: 2px solid #5285A6;
        }

        /* ── 列表控件 ── */
        QListWidget {
            background-color: #272727;
            border: 1px solid #272727;
            border-radius: 3px;
            padding: 4px;
        }
        
        /* ── 右键菜单 ── */
        QMenu {
            background-color: #454545;
        }
        QMenu::item {
            background: transparent;
        }
        QMenu::item:selected {
            background-color: #5285A6;
            color: #ffffff;
        }
        QMenu::item:disabled {
            color: #666666;
        }
        QMenu::separator {
            height: 1px;
            background-color: #555555;
            margin: 4px 8px;
        }
        QMenu QLabel[menuHeader="true"] {
            color: #FFD700;
            font-weight: bold;
            font-size: 11px;
            background: transparent;
        }

        /* ── 滚动条 ── */
        QScrollBar:vertical {
            background-color: #2b2b2b;
            width: 10px;
            border-radius: 5px;
        }
        QScrollBar::handle:vertical {
            background-color: #555555;
            border-radius: 5px;
            min-height: 20px;
        }
        QScrollBar::handle:vertical:hover {
            background-color: #777777;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        QScrollBar:horizontal {
            background-color: #2b2b2b;
            height: 10px;
            border-radius: 5px;
        }
        QScrollBar::handle:horizontal {
            background-color: #555555;
            border-radius: 5px;
            min-width: 20px;
        }
        QScrollBar::handle:horizontal:hover {
            background-color: #777777;
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0px;
        }

        """

        widget.setStyleSheet(style)

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
