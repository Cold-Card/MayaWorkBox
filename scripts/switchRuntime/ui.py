# coding=utf-8
import os.path
try:
    from PySide2.QtWidgets import *
    from PySide2.QtCore import *
except ImportError:
    from PySide6.QtWidgets import *
    from PySide6.QtCore import *

from . import tools


def q_prefix(text, width):
    prefix = QLabel(text)
    prefix.setFixedWidth(width)
    prefix.setAlignment(Qt.AlignRight)
    return prefix


def q_add(layout, *elements):
    for elem in elements:
        if isinstance(elem, QLayout):
            layout.addLayout(elem)
        elif isinstance(elem, QWidget):
            layout.addWidget(elem)
    return layout


def q_button(text, action):
    but = QPushButton(text)
    but.clicked.connect(action)
    return but


qss = """
QWidget{
    font-size: 16px;
    font-family: 楷体;
}
"""


class Tool(QDialog):

    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.setWindowTitle(u"实时切换")
        self.setMinimumWidth(250)
        self.setStyleSheet(qss)
        self.setLayout(q_add(
            QVBoxLayout(),
            q_button(u"adv标准人体", tools.adv_biped),
            q_button(u"创建手臂集合", tools.switch.Arm.create_set),
            q_add(
                QHBoxLayout(),
                q_button(u"开启实时切换", tools.open_switch),
                q_button(u"关闭实时切换", tools.close_switch),
            ),
            q_add(
                QHBoxLayout(),
                q_button(u"开启自动启动", tools.open_auto_switch),
                q_button(u"关闭自动启动", tools.close_auto_switch),
            ),
            q_add(
                QHBoxLayout(),
                q_button(u"开启帧同步", tools.open_key_frame_post),
                q_button(u"关闭帧同步", tools.close_key_frame_post),
            ),
        ))


window = None


def get_app():
    top = QApplication.activeWindow()
    if top is None:
        return
    while True:
        parent = top.parent()
        if parent is None:
            return top
        top = parent


def show():
    global window
    if window is None:
        window = Tool(parent=get_app())
    window.showNormal()


def doit():
    show()
