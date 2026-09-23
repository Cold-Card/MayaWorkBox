# -*- coding: utf-8 -*-
from PySide2.QtCore import *
from PySide2.QtWidgets import *

def show_menu(event, context_menu, parent):
    u'''
    显示子菜单，并且位置在鼠标附近
    '''
    # 获取鼠标位置
    x = event.x()
    y = event.y()
    # 将位置转换为全局坐标
    global_pos = parent.mapToGlobal(QPoint(x, y))
    # 显示菜单并设置位置
    context_menu.exec_(global_pos)

def create_context_menu1(component, menu_items, functions):
    u'''
    创建右键子菜单
    component：组件对象
    menu_items：子菜单名称列表
    functions：函数名称列表
    创建子菜单，子菜单名称和功能，与 menu_items, functions的参数一一对应
    '''
    # 创建右键菜单
    context_menu = QMenu(component)

    # 创建每个菜单项，并关联执行的函数
    for item_text, func in zip(menu_items, functions):
        action = QAction(item_text, component)
        action.triggered.connect(func)
        context_menu.addAction(action)

    # 监听组件的右键点击事件
    component.setContextMenuPolicy(Qt.CustomContextMenu)
    component.customContextMenuRequested.connect(lambda event: show_menu(event, context_menu, component))

