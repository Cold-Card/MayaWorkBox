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
        label.setStyleSheet('color:#8c8c8c; font: bold 8px;')
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
            font-family: "Microsoft YaHei", "PingFang SC", "Segoe UI", sans-serif;
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
            color: #cccccc;
            background: transparent;
            font-weight: bold;
            font-size: 12px;
        }
    
        /* ── 按钮 ── */
        QPushButton {
            background-color: #5A5F68;
            color: #e0e0e0;
            border-radius: 6px;
            padding: 4px 4px;
            font-weight: bold;
            font-size: 12px;
        }
        QPushButton:hover {
            background-color: #6C7380;
        }
        QPushButton:pressed {
            background-color: #4A4E57;
        }
        QPushButton:disabled {
            background-color: #333333;
            color: #666666;
        }
    
        /* 主要操作按钮（白色调） */
        QPushButton[primary="true"] {
            color: #000000;
            background-color: #ADADAD;
            border-radius: 6px;
            padding: 4px 4px;
            font-weight: bold;
            font-size: 12px;            
        }
        QPushButton[primary="true"]:hover {
            background-color: #DFDFDF;
        }
        QPushButton[primary="true"]:pressed {
            background-color: #838383;
        }
        QPushButton[primary="true"]:disabled {
            background-color: #333333;
            color: #666666;
        }
    
        /* 次要操作按钮（灰色调） */
        QPushButton[secondary="true"] {
            background-color: #5a5f68;
            color: #e0e0e0;
        }
        QPushButton[secondary="true"]:hover {
            background-color: #6C7380;
        }
        QPushButton[secondary="true"]:pressed {
            background-color: #4A4E57;
        }
        QPushButton[secondary="true"]:disabled {
            background-color: #333333;
            color: #666666;
        }
    
        /* 绿字按钮 */
        QPushButton[primary_green="true"] {
            color: #2F7A00;
            background-color: #ADADAD;
        }
        QPushButton[primary_green="true"]:hover {
            background-color: #DFDFDF;
        }
        QPushButton[primary_green="true"]:pressed {
            background-color: #838383;
        }
        QPushButton[primary_green="true"]:disabled {
            background-color: #333333;
            color: #666666;
        }
    
        /* 红字按钮 */
        QPushButton[primary_red="true"] {
            color: #FF0000;
            background-color: #ADADAD;
        }
        QPushButton[primary_red="true"]:hover {
            background-color: #DFDFDF;
        }
        QPushButton[primary_red="true"]:pressed {
            background-color: #838383;
        }
        QPushButton[primary_red="true"]:disabled {
            background-color: #333333;
            color: #666666;
        }
    
        /* 下拉框 */
        QComboBox {
            background-color: #2E2E2E;
            border: 1px solid #5a5a5a;
            border-radius: 3px;
            padding: 3px 6px;
            outline: none;
        }
        QComboBox::drop-down {
            width: 20;
            background-color: #5a5a5a;
        }
        QComboBox QAbstractItemView {
            background-color: #2E2E2E;
            selection-background-color: #5285A6;
            border: 1px solid #5a5a5a;
            outline: none;
            padding: 3px 3px;
        }
        /* ── 输入框 / 搜索框 ── */
        QLineEdit, QTextEdit {
            background-color: #272727;
            border: 1px solid #272727;
            border-radius: 3px;
            padding: 3px;
        }
        QLineEdit:focus, QTextEdit:focus {
            border: 2px solid #5285A6;
        }
        /* ── 列表控件 ── */
        QListWidget {
            background-color: #272727;
            border: 1px solid #272727;
            border-radius: 3px;
            padding: 3px;
            outline: none;
        }
        QListWidget::item {
            padding: 2px 5px;
            border-radius: 3px;
        }
        QListWidget::item:selected {
            background-color: #5285A6;
            color: #ffffff;
        }
        QListWidget::item:hover {
            background-color: #3a5a6a;
        }
        /* ── 右键菜单 ── */
        QMenu {
            background-color: #3a3a3a;
            border: 1px solid #4a4a4a;
            padding: 4px;
        }
        QMenu::item {
            padding: 4px 20px;
            border-radius: 4px;
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
        }
        /* ── 滚动条 ── */
        QScrollBar:vertical {
            background-color: #2b2b2b;
            width: 6px;
            border-radius: 3px;
        }
        QScrollBar::handle:vertical {
            background-color: #555555;
            border-radius: 3px;
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
            height: 6px;
            border-radius: 3px;
        }
        QScrollBar::handle:horizontal {
            background-color: #555555;
            border-radius: 3px;
            min-width: 20px;
        }
        QScrollBar::handle:horizontal:hover {
            background-color: #777777;
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0px;
        }
        /* ── 复选框 ── */
        QCheckBox {
            background: transparent;
            spacing: 6px;
        }
        QCheckBox::indicator {
            width: 16px;
            height: 16px;
            border-radius: 4px;
            background-color: #222222;
            border: 1px solid #4a4a4a;
        }
        QCheckBox::indicator:checked {
            background-color: #4a7b8f;
            border: 1px solid #4a7b8f;
        }
        QCheckBox::indicator:hover {
            border-color: #5285A6;
        }
    
        /* ── 滑块 ── */
        QSlider {
            background: transparent;
        }
        QSlider::groove:horizontal {
            background-color: #272727;
            border: 1px solid #272727;
            height: 6px;
            border-radius: 3px;
        }
        QSlider::handle:horizontal {
            background: #4a7b8f;
            border: none;
            width: 14px;
            margin: -4px 0;
            border-radius: 7px;
        }
        QSlider::handle:horizontal:hover {
            background: #6a9fb5;
        }
        QSlider::sub-page:horizontal {
            background: #4a7b8f;
            border-radius: 3px;
        }
    
        /* ── 数字框 ── */
        QSpinBox {
            background-color: #272727;
            border: 1px solid #272727;
            border-radius: 3px;
            padding: 3px;
        }
        QSpinBox:focus {
            border: 2px solid #5285A6;
        }
        QSpinBox::up-button, QSpinBox::down-button {
            width: 0;
        }
    
        /* ── 标签页 ── */
        QTabWidget::pane {
            border-top: 1px solid #4E4E4E;
            background-color: #353535;
            padding-top: 3px;
        }
        QTabBar::tab {
            background-color: #353535;
            border: 1px solid #353535;
            border-bottom: none;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            padding: 8px 16px;
            color: #8a9aa8;
            font-weight: bold;
            font-size: 12px;
        }
        QTabBar::tab:selected {
            background-color: #454545;
            color: #5285A6;
            border-bottom: 2px solid #5285A6;
        }
        QTabBar::tab:hover {
            background-color: #454545;
        }
        QTabBar::tab:!selected {
            margin-top: 2px;
        }
    
        /* ── tip ── */
        QToolTip {
            background-color: #D8D8BA;
            border: 1px solid #D8D8BA;
            padding: 2px;
            color: #202020;
        }
    
        /* ── 堆叠窗口部件 ── */
        QStackedWidget {
            background: transparent;
        }
        QStackedWidget > QWidget {
            background: transparent;
            border: none;
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
