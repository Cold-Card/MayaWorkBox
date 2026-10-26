# -*- coding: utf-8 -*-
"""
Maya 工具：根据物体名和属性名，查找并选择连接的上游/下游节点
支持 PySide2 / PySide6
"""

import maya.cmds as cmds
import maya.OpenMayaUI as omui

try:
    from PySide6 import QtWidgets, QtCore, QtGui
    from shiboken6 import wrapInstance
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui
    from shiboken2 import wrapInstance

try:
    import Qt_style
except ImportError:
    pass
    
def maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    if ptr:
        return wrapInstance(int(ptr), QtWidgets.QWidget)
    return None


# ==========================================================
#                      核心逻辑
# ==========================================================

def _expand_attrs_to_plugs(obj, attrs):
    """将属性名列表展开为完整 plug 列表（复合属性自动展开为子属性）"""
    plugs = []
    for attr in attrs:
        if '.' in attr:
            node, attr_name = attr.rsplit('.', 1)
            full = attr
        else:
            node, attr_name = obj, attr
            full = '{}.{}'.format(obj, attr)

        if not cmds.objExists(full):
            cmds.warning(u'属性不存在或不可连接: {}'.format(full))
            continue

        children = cmds.attributeQuery(attr_name, node=node, listChildren=True)
        if children:
            for child in children:
                child_plug = '{}.{}'.format(node, child)
                if cmds.objExists(child_plug):
                    plugs.append(child_plug)
        else:
            plugs.append(full)
    return plugs


def find_connected_nodes(obj, attrs, direction='downstream',
                         include_shapes=False, skip_conversion=True):
    """查找连接到指定物体属性的节点（单层，不递归）"""
    if not cmds.objExists(obj):
        cmds.warning(u'物体不存在: {}'.format(obj))
        return []

    if isinstance(attrs, str):
        attrs = [attrs]

    if direction not in ('downstream', 'upstream'):
        raise ValueError("direction 必须是 'downstream' 或 'upstream'")

    plugs = _expand_attrs_to_plugs(obj, attrs)
    if not plugs:
        return []

    if direction == 'upstream':
        connections = cmds.listConnections(
            plugs, source=True, destination=False,
            skipConversionNodes=skip_conversion, shapes=include_shapes
        ) or []
    else:
        connections = cmds.listConnections(
            plugs, source=False, destination=True,
            skipConversionNodes=skip_conversion, shapes=include_shapes
        ) or []

    seen = set()
    result = []
    for n in connections:
        if n not in seen:
            seen.add(n)
            result.append(n)
    return result


# ==========================================================
#                        UI
# ==========================================================

class FindConnectionUI(QtWidgets.QDialog):

    def __init__(self, parent=None):
        super(FindConnectionUI, self).__init__(parent or maya_main_window())
        self.setWindowTitle('查找连接节点')
        self.setWindowFlags(QtCore.Qt.Window |
            QtCore.Qt.WindowMinimizeButtonHint |
            QtCore.Qt.WindowMaximizeButtonHint |
            QtCore.Qt.WindowCloseButtonHint)
        try:
            Qt_style.apply_style(self)  # 应用优化后的样式表
        except Exception:
            cmds.warning("未找到样式表，使用默认样式")
        #self.setMinimumWidth(440)
        self._build_ui()
        self._connect_signals()
        self.refresh_from_selection()

    # ---------------- 界面构建 ----------------
    def _build_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        input_group = QtWidgets.QGroupBox(u'输入')
        form = QtWidgets.QFormLayout(input_group)
        form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        form.setSpacing(6)

        obj_row = QtWidgets.QHBoxLayout()
        obj_row.setSpacing(4)
        self.obj_edit = QtWidgets.QLineEdit()
        self.obj_edit.setPlaceholderText(u'例如: pCube1')
        self.obj_btn = QtWidgets.QPushButton(u'◀ 当前选择')
        self.obj_btn.setFixedWidth(96)
        self.obj_btn.setToolTip(u'从当前选择获取物体名')
        obj_row.addWidget(self.obj_edit)
        obj_row.addWidget(self.obj_btn)
        form.addRow(u'物体:', obj_row)

        attr_row = QtWidgets.QHBoxLayout()
        attr_row.setSpacing(4)
        self.attr_edit = QtWidgets.QLineEdit()
        self.attr_edit.setPlaceholderText(u'例如: translateX,translateY  或  translate')
        self.attr_btn = QtWidgets.QPushButton(u'◀ 通道盒')
        self.attr_btn.setFixedWidth(96)
        self.attr_btn.setToolTip(u'从通道盒当前选中属性获取')
        attr_row.addWidget(self.attr_edit)
        attr_row.addWidget(self.attr_btn)
        form.addRow(u'属性:', attr_row)

        main_layout.addWidget(input_group)

        opt_group = QtWidgets.QGroupBox(u'选项')
        opt_layout = QtWidgets.QVBoxLayout(opt_group)
        opt_layout.setSpacing(6)

        dir_row = QtWidgets.QHBoxLayout()
        dir_row.setSpacing(10)
        dir_row.addWidget(QtWidgets.QLabel(u'方向:'))
        self.down_radio = QtWidgets.QRadioButton(u'下游 (输出 →)')
        self.up_radio = QtWidgets.QRadioButton(u'上游 (← 输入)')
        self.down_radio.setChecked(True)
        dir_row.addWidget(self.down_radio)
        dir_row.addWidget(self.up_radio)
        dir_row.addStretch()
        opt_layout.addLayout(dir_row)

        chk_row = QtWidgets.QHBoxLayout()
        chk_row.setSpacing(12)
        self.shape_chk = QtWidgets.QCheckBox(u'包含 shape')
        self.skip_conv_chk = QtWidgets.QCheckBox(u'跳过转换节点')
        self.skip_conv_chk.setChecked(True)
        self.skip_conv_chk.setToolTip(u'跳过 unitConversion 等中间节点')
        chk_row.addWidget(self.shape_chk)
        chk_row.addWidget(self.skip_conv_chk)
        chk_row.addStretch()
        opt_layout.addLayout(chk_row)

        main_layout.addWidget(opt_group)

        btn_row = QtWidgets.QHBoxLayout()
        btn_row.setSpacing(6)
        self.find_btn = QtWidgets.QPushButton(u'查找并选择')
        self.find_btn.setMinimumHeight(30)
        self.find_btn.setStyleSheet('QPushButton { font-weight: bold; }')
        self.add_sel_chk = QtWidgets.QCheckBox(u'附加选择')
        self.add_sel_chk.setToolTip(u'不替换当前选择，而是追加')
        btn_row.addWidget(self.find_btn, 1)
        btn_row.addWidget(self.add_sel_chk)
        main_layout.addLayout(btn_row)

        res_group = QtWidgets.QGroupBox(u'结果')
        res_layout = QtWidgets.QVBoxLayout(res_group)
        res_layout.setSpacing(4)

        self.result_list = QtWidgets.QListWidget()
        self.result_list.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.result_list.setAlternatingRowColors(True)
        self.result_list.setMinimumHeight(150)
        self.result_list.setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.CustomContextMenu
        )
        res_layout.addWidget(self.result_list)

        bottom_row = QtWidgets.QHBoxLayout()
        self.status_label = QtWidgets.QLabel(u'就绪')
        self.status_label.setStyleSheet('color: #888888;')
        bottom_row.addWidget(self.status_label, 1)
        # —— 让布局忽略文本长度对窗口的影响 ——
        self.status_label.setSizePolicy(
            QtWidgets.QSizePolicy.Ignored,
            QtWidgets.QSizePolicy.Preferred,
        )
        self.status_label.setMinimumWidth(0)

        self.clear_btn = QtWidgets.QPushButton(u'清空')
        self.clear_btn.setFixedWidth(60)
        bottom_row.addWidget(self.clear_btn)
        res_layout.addLayout(bottom_row)

        main_layout.addWidget(res_group, 1)

    # ---------------- 信号连接 ----------------
    def _connect_signals(self):
        self.obj_btn.clicked.connect(self.refresh_from_selection)
        self.attr_btn.clicked.connect(self.pull_channelbox_attrs)
        self.find_btn.clicked.connect(self.do_find)
        self.clear_btn.clicked.connect(self.clear_results)
        # 用 itemSelectionChanged：单击 / Ctrl / Shift / 拖拽框选都会触发
        self.result_list.itemSelectionChanged.connect(self._on_selection_changed)
        self.result_list.customContextMenuRequested.connect(self._show_context_menu)
        self.obj_edit.returnPressed.connect(self.do_find)
        self.attr_edit.returnPressed.connect(self.do_find)

    # ---------------- 辅助方法 ----------------
    def _set_status(self, text):
        """设置状态文本；不改变窗口大小，完整内容放到 tooltip"""
        self.status_label.setText(text)
        self.status_label.setToolTip(text)

    def refresh_from_selection(self):
        sel = cmds.ls(sl=True) or []
        if sel:
            self.obj_edit.setText(sel[0])
            self._set_status(u'已从选择获取物体: {}'.format(sel[0]))
        else:
            self._set_status(u'没有选中任何物体')

    def pull_channelbox_attrs(self):
        attrs = []
        try:
            attrs = cmds.channelBox(
                'mainChannelBox', q=True, selectedMainAttributes=True
            ) or []
        except Exception:
            pass

        if not attrs:
            try:
                attrs = cmds.channelBox(
                    'mainChannelBox', q=True, selectedShapeAttributes=True
                ) or []
            except Exception:
                pass

        if attrs:
            self.attr_edit.setText(','.join(attrs))
            self._set_status(u'已从通道盒获取属性: {}'.format(', '.join(attrs)))
        else:
            self._set_status(u'通道盒未选中属性，请先在通道盒中高亮属性')

    # ---------------- 主逻辑 ----------------
    def do_find(self):
        obj = self.obj_edit.text().strip()
        attr_text = self.attr_edit.text().strip()

        if not obj:
            cmds.warning(u'请输入物体名')
            return
        if not cmds.objExists(obj):
            cmds.warning(u'物体不存在: {}'.format(obj))
            self._set_status(u'物体不存在: {}'.format(obj))
            return
        if not attr_text:
            cmds.warning(u'请输入属性名')
            return

        attrs = [a.strip() for a in attr_text.replace(';', ',').split(',') if a.strip()]

        direction = 'upstream' if self.up_radio.isChecked() else 'downstream'
        include_shapes = self.shape_chk.isChecked()
        skip_conv = self.skip_conv_chk.isChecked()
        add = self.add_sel_chk.isChecked()

        self.result_list.clear()
        nodes = find_connected_nodes(
            obj, attrs,
            direction=direction,
            include_shapes=include_shapes,
            skip_conversion=skip_conv,
        )

        if not nodes:
            self._set_status(u'未找到连接节点')
            return

        for n in nodes:
            item = QtWidgets.QListWidgetItem(n)
            try:
                ntype = cmds.nodeType(n)
                item.setToolTip(u'{}\n类型: {}'.format(n, ntype))
            except Exception:
                pass
            self.result_list.addItem(item)

        cmds.select(nodes, add=add, replace=not add)

        dir_txt = u'上游' if direction == 'upstream' else u'下游'
        self._set_status(
            u'找到 {} 个{}节点 ({} -> {})'.format(len(nodes), dir_txt, obj, attr_text)
        )

    # ---------------- 结果区操作 ----------------
    def clear_results(self):
        # 清空前先断开信号，避免清空时触发选择同步
        self.result_list.itemSelectionChanged.disconnect(self._on_selection_changed)
        self.result_list.clear()
        self.result_list.itemSelectionChanged.connect(self._on_selection_changed)
        self._set_status(u'已清空结果')

    def _on_selection_changed(self):
        """列表选中项变化（单击 / Ctrl / Shift / 拖拽框选）→ 同步到 Maya 选择"""
        nodes = [i.text() for i in self.result_list.selectedItems()]
        if nodes:
            cmds.select(nodes, replace=True)

    def _show_context_menu(self, pos):
        menu = QtWidgets.QMenu(self)
        act_copy = menu.addAction(u'复制名字')
        menu.addSeparator()
        act_delete = menu.addAction(u'从列表移除')

        action = menu.exec_(self.result_list.mapToGlobal(pos))
        if action == act_copy:
            names = [i.text() for i in self.result_list.selectedItems()]
            if names:
                QtWidgets.QApplication.clipboard().setText('\n'.join(names))
                self._set_status(u'已复制 {} 个名字到剪贴板'.format(len(names)))
        elif action == act_delete:
            for it in self.result_list.selectedItems():
                self.result_list.takeItem(self.result_list.row(it))


# ==========================================================
#                       入口
# ==========================================================

def show_ui():
    global findConnection_UI
    try:
        if findConnection_UI is not None:
            findConnection_UI.close()
            findConnection_UI.deleteLater()
    except (NameError, RuntimeError):
        pass
    findConnection_UI = FindConnectionUI()
    findConnection_UI.show()

if __name__ == '__main__':
    show_ui()