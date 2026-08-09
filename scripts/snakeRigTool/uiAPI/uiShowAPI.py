# -*- coding: utf 8 -*-
from PySide2 import QtWidgets
import maya.OpenMayaUI as omui
import shiboken2

def get_maya_main_window():
    u'''
    获取maya主窗口对象
    '''
    main_window_ptr = omui.MQtUtil.mainWindow()
    return shiboken2.wrapInstance(int(main_window_ptr), QtWidgets.QMainWindow)

def deleteMayaSurplusUI(windowName):
    u'''
    删除maya主窗口子对象中名为windowName的窗口，
    由于某些窗口不具备 objectName() 这个方法，所以会导致报错
    这里用try过滤掉
    '''
    for child in get_maya_main_window().children():
        if child.objectName() == windowName:
            child.deleteLater()