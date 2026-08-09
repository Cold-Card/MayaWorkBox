import maya.cmds as cmds
from maya import OpenMayaUI as omui
# 兼容 PySide2 (Maya 2017-2024) 和 PySide6 (Maya 2025+)
try:
    from PySide6 import QtWidgets, QtCore
    from shiboken6 import wrapInstance
except ImportError:
    from PySide2 import QtWidgets, QtCore
    from shiboken2 import wrapInstance

def get_maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)

class SpaceSwitchUI(QtWidgets.QDialog):
    def __init__(self, parent=get_maya_main_window()):
        super(SpaceSwitchUI, self).__init__(parent)

        self.setWindowTitle("空间切换工具")
        #self.setMinimumWidth(450)
        #self.setMinimumHeight(350)
        #self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)

        # 设置全局样式表
        self.setStyleSheet("""
            QDialog {
                background-color: #3a3a3a;
            }
            QLabel {
                color: #f0f0f0;
                font-size: 12px;
            }
            QLabel#title {
                font-size: 14px;
                font-weight: bold;
                color: #ffaa55;
                margin-bottom: 5px;
            }
            QLabel#info {
                color: #aaffaa;
                background-color: #2a2a2a;
                padding: 5px;
                border-radius: 4px;
            }
            QLabel#warning {
                color: #ffaa55;
            }

            /* 按钮通用样式 */
            QPushButton {
                background-color: #5a5a5a;
                color: white;
                border: 1px solid #7a7a7a;
                border-radius: 5px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #6a6a6a;
                border-color: #9a9a9a;
            }
            QPushButton:pressed {
                background-color: #4a4a4a;
            }
            /* 禁用按钮样式 - 变灰、文字变淡 */
            QPushButton:disabled {
                background-color: #3a3a3a;
                border-color: #5a5a5a;
                color: #888888;
            }
            QPushButton#loadBtn {
                background-color: #2c6e9e;
                border-color: #3e8ec0;
                font-weight: bold;
            }
            QPushButton#loadBtn:hover {
                background-color: #3e7eb0;
            }
            QPushButton#loadBtn:disabled {
                background-color: #2a4a6a;
                border-color: #3a5a7a;
                color: #88aacc;
            }

            /* 数值输入框 - 隐藏上下箭头 */
            QDoubleSpinBox {
                background-color: #4a4a4a;
                color: white;
                border: 1px solid #6a6a6a;
                border-radius: 3px;
                padding: 4px;
                padding-right: 4px;
                min-height: 20px;
                selection-background-color: #2c6e9e;
                outline: none;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                width: 0;
                height: 0;
            }

            /* 下拉框 */
            QComboBox {
                background-color: #4a4a4a;
                color: white;
                border: 1px solid #6a6a6a;
                border-radius: 3px;
                padding: 4px;
                min-height: 20px;
                outline: none;
            }
            QComboBox::drop-down {
                border: none;
                width: 0;
                background-color: #5a5a5a;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }
            QComboBox QAbstractItemView {
                background-color: #4a4a4a;
                color: white;
                selection-background-color: #2c6e9e;
                border: 1px solid #6a6a6a;
                outline: none;
            }

            /* 滑块 */
            QSlider::groove:horizontal {
                height: 6px;
                background: #5a5a5a;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #ffaa55;
                width: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            QSlider::sub-page:horizontal {
                background: #2c6e9e;
                border-radius: 3px;
            }

            QGroupBox {
                color: #ffaa55;
                font-weight: bold;
                border: 1px solid #5a5a5a;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

        self.current_ctrl = None
        self.current_attr = None
        self.attr_type = None
        self.enum_list = []
        self._updating = False

        self.create_widgets()
        self.create_layouts()
        self.create_connections()

        self.on_load_clicked()

    def create_widgets(self):
        # 标题
        self.title_label = QtWidgets.QLabel("空间切换助手")
        self.title_label.setObjectName("title")
        self.title_label.setAlignment(QtCore.Qt.AlignCenter)

        # 信息标签
        self.info_label = QtWidgets.QLabel("⚡ 请选择控制器并在通道盒中选中属性")
        self.info_label.setObjectName("info")
        self.info_label.setWordWrap(True)

        # 控制器和属性显示
        self.ctrl_label = QtWidgets.QLabel("📦 控制器: --")
        self.attr_label = QtWidgets.QLabel("🏷️ 属性: --")

        # 加载按钮
        self.load_btn = QtWidgets.QPushButton("↻ 从当前选择加载")
        self.load_btn.setObjectName("loadBtn")
        self.load_btn.setFixedHeight(32)

        # 动态区域容器 (GroupBox)
        self.dynamic_group = QtWidgets.QGroupBox("空间切换控件")
        self.dynamic_layout = QtWidgets.QVBoxLayout(self.dynamic_group)
        self.dynamic_layout.setContentsMargins(10, 15, 10, 10)

        # 控件引用
        self.value_spinbox = None
        self.value_slider = None
        self.min_btn = None
        self.max_btn = None
        self.enum_combo = None

    def create_layouts(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(15, 15, 15, 15)

        main_layout.addWidget(self.title_label)
        main_layout.addWidget(self.info_label)

        # 信息框
        info_frame = QtWidgets.QFrame()
        info_frame.setStyleSheet("background-color: #2a2a2a; border-radius: 6px;")
        info_layout = QtWidgets.QVBoxLayout(info_frame)
        info_layout.addWidget(self.ctrl_label)
        info_layout.addWidget(self.attr_label)
        main_layout.addWidget(info_frame)

        main_layout.addWidget(self.load_btn)
        main_layout.addWidget(self.dynamic_group)
        main_layout.addStretch()

    def create_connections(self):
        self.load_btn.clicked.connect(self.on_load_clicked)

    def clear_dynamic_area(self):
        # 清空布局中的所有子项
        while self.dynamic_layout.count():
            item = self.dynamic_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())
                item.layout().deleteLater()
        self.value_spinbox = None
        self.value_slider = None
        self.min_btn = None
        self.max_btn = None
        self.enum_combo = None
        self.dynamic_group.update()

    def _clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self._clear_layout(child.layout())
                child.layout().deleteLater()

    def on_load_clicked(self):
        ctrl, attr = self.get_selected_ctrl_and_attr()
        if not ctrl or not attr:
            self.info_label.setText("⚠️ 错误: 请选择一个控制器，并在通道盒中选中一个属性")
            self.info_label.setStyleSheet("color: #ffaa55; background-color: #2a2a2a; padding: 5px; border-radius: 4px;")
            self.clear_dynamic_area()
            return

        self.current_ctrl = ctrl
        self.current_attr = attr
        self.ctrl_label.setText(f"📦 控制器: {ctrl}")
        self.attr_label.setText(f"🏷️ 属性: {attr}")

        attr_info = self.get_attribute_info(ctrl, attr)
        if attr_info is None:
            self.info_label.setText("❌ 错误: 无法读取属性信息")
            self.clear_dynamic_area()
            return

        self.attr_type = attr_info['type']
        self.clear_dynamic_area()

        if self.attr_type == 'float':
            self.build_float_ui(ctrl, attr, attr_info)
            self.info_label.setText("✅ 数值属性 | 使用滑块或 Min/Max 切换空间")
            self.info_label.setStyleSheet("color: #aaffaa; background-color: #2a2a2a; padding: 5px; border-radius: 4px;")
        elif self.attr_type == 'enum':
            self.enum_list = attr_info['enum_names']
            self.build_enum_ui(ctrl, attr, attr_info)
            self.info_label.setText("✅ 枚举属性 | 点击下方选项切换空间")
            self.info_label.setStyleSheet("color: #aaffaa; background-color: #2a2a2a; padding: 5px; border-radius: 4px;")
        else:
            self.info_label.setText("❌ 错误: 不支持的属性类型（仅支持 float/enum）")
            return

        self.sync_ui_from_attr()

    def get_selected_ctrl_and_attr(self):
        sel = cmds.ls(selection=True)
        if not sel:
            cmds.warning("请先选择一个控制器")
            return None, None
        ctrl = sel[0]

        attr = cmds.channelBox('mainChannelBox', query=True, selectedMainAttributes=True)
        if not attr:
            cmds.warning("请在通道盒中选中一个属性")
            return None, None
        attr_name = attr[0]
        return ctrl, attr_name

    def get_attribute_info(self, node, attr):
        info = {}
        try:
            is_enum = cmds.attributeQuery(attr, node=node, enum=True)
        except:
            is_enum = False

        if is_enum:
            enum_raw = cmds.attributeQuery(attr, node=node, listEnum=True)[0]
            enum_names = enum_raw.split(':')
            info['type'] = 'enum'
            info['enum_names'] = enum_names
            return info
        else:
            try:
                cmds.getAttr(f"{node}.{attr}")
            except:
                return None
            info['type'] = 'float'
            has_min = cmds.attributeQuery(attr, node=node, minExists=True)
            has_max = cmds.attributeQuery(attr, node=node, maxExists=True)
            info['min'] = cmds.attributeQuery(attr, node=node, min=True)[0] if has_min else None
            info['max'] = cmds.attributeQuery(attr, node=node, max=True)[0] if has_max else None
            return info

    def build_float_ui(self, node, attr, attr_info):
        self.value_spinbox = QtWidgets.QDoubleSpinBox()
        self.value_spinbox.setDecimals(4)
        self.value_spinbox.setRange(-1e6, 1e6)
        self.value_spinbox.valueChanged.connect(self.on_float_value_changed)

        self.value_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.value_slider.setRange(0, 1000)
        self.value_slider.valueChanged.connect(self.on_slider_moved)

        self.min_btn = QtWidgets.QPushButton("最小值")
        self.max_btn = QtWidgets.QPushButton("最大值")
        self.min_btn.clicked.connect(self.on_min_clicked)
        self.max_btn.clicked.connect(self.on_max_clicked)

        min_val = attr_info.get('min')
        max_val = attr_info.get('max')
        self.attr_min = min_val
        self.attr_max = max_val
        
        if min_val is None or max_val is None:
            self.min_btn.setToolTip("属性未定义最小值，无法使用")
            self.max_btn.setToolTip("属性未定义最大值，无法使用")

        current_val = cmds.getAttr(f"{node}.{attr}")
        if isinstance(current_val, (list, tuple)):
            current_val = current_val[0] if current_val else 0.0

        if min_val is not None and max_val is not None and min_val < max_val:
            self.value_spinbox.setRange(min_val, max_val)
            self._slider_min = min_val
            self._slider_max = max_val
        else:
            margin = max(1.0, abs(current_val) * 0.2) if current_val != 0 else 10.0
            low = current_val - margin
            high = current_val + margin
            self.value_spinbox.setRange(low, high)
            self._slider_min = low
            self._slider_max = high
            self.min_btn.setEnabled(False)
            self.max_btn.setEnabled(False)

        self._updating = True
        self.value_spinbox.setValue(current_val)
        self._update_slider_from_value(current_val)
        self._updating = False

        # 布局
        layout = QtWidgets.QFormLayout()
        layout.addRow("数值:", self.value_spinbox)
        layout.addRow("滑块:", self.value_slider)
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addWidget(self.min_btn)
        btn_layout.addWidget(self.max_btn)
        layout.addRow("快捷:", btn_layout)

        self.dynamic_layout.addLayout(layout)

    def build_enum_ui(self, node, attr, attr_info):
        enum_names = attr_info['enum_names']
        self.enum_combo = QtWidgets.QComboBox()
        self.enum_combo.addItems(enum_names)
        self.enum_combo.currentIndexChanged.connect(self.on_enum_index_changed)

        label = QtWidgets.QLabel("选择跟随空间:")
        label.setStyleSheet("color: #cccccc;")
        self.dynamic_layout.addWidget(label)
        self.dynamic_layout.addWidget(self.enum_combo)

        current_val = cmds.getAttr(f"{node}.{attr}")
        try:
            idx = int(current_val)
            if 0 <= idx < len(enum_names):
                self.enum_combo.setCurrentIndex(idx)
        except:
            pass

    def sync_ui_from_attr(self):
        if not self.current_ctrl or not self.current_attr:
            return
        full_attr = f"{self.current_ctrl}.{self.current_attr}"
        try:
            current_val = cmds.getAttr(full_attr)
            if isinstance(current_val, (list, tuple)):
                current_val = current_val[0]
        except:
            return

        self._updating = True
        if self.attr_type == 'float' and self.value_spinbox:
            self.value_spinbox.setValue(current_val)
            self._update_slider_from_value(current_val)
        elif self.attr_type == 'enum' and self.enum_combo:
            idx = int(current_val) if isinstance(current_val, (int, float)) else 0
            if 0 <= idx < self.enum_combo.count():
                self.enum_combo.setCurrentIndex(idx)
        self._updating = False

    def _update_slider_from_value(self, value):
        if not self.value_slider:
            return
        min_v = self._slider_min
        max_v = self._slider_max
        if max_v - min_v != 0:
            t = (value - min_v) / (max_v - min_v)
            slider_val = int(t * 1000)
            slider_val = max(0, min(1000, slider_val))
            self.value_slider.blockSignals(True)
            self.value_slider.setValue(slider_val)
            self.value_slider.blockSignals(False)

    def _get_value_from_slider(self, slider_val):
        min_v = self._slider_min
        max_v = self._slider_max
        t = slider_val / 1000.0
        return min_v + t * (max_v - min_v)

    def preserve_transform_and_set_attr(self, value):
        if not self.current_ctrl:
            return
        ctrl = self.current_ctrl
        full_attr = f"{self.current_ctrl}.{self.current_attr}"
        pos = cmds.xform(ctrl, query=True, translation=True, worldSpace=True)
        rot = cmds.xform(ctrl, query=True, rotation=True, worldSpace=True)
        try:
            cmds.setAttr(full_attr, value)
        except Exception as e:
            cmds.warning(f"设置属性失败: {e}")
            return
        cmds.xform(ctrl, translation=pos, rotation=rot, worldSpace=True)
        self.sync_ui_from_attr()

    def on_float_value_changed(self, new_val):
        if self._updating:
            return
        self.preserve_transform_and_set_attr(new_val)
        if self.value_slider:
            self._updating = True
            self._update_slider_from_value(new_val)
            self._updating = False

    def on_slider_moved(self, slider_val):
        if self._updating:
            return
        real_val = self._get_value_from_slider(slider_val)
        if self.value_spinbox:
            self.value_spinbox.blockSignals(True)
            self.value_spinbox.setValue(real_val)
            self.value_spinbox.blockSignals(False)
        self.preserve_transform_and_set_attr(real_val)

    def on_min_clicked(self):
        if self.attr_min is not None:
            self.preserve_transform_and_set_attr(self.attr_min)
        else:
            cmds.warning("该属性未定义最小值")

    def on_max_clicked(self):
        if self.attr_max is not None:
            self.preserve_transform_and_set_attr(self.attr_max)
        else:
            cmds.warning("该属性未定义最大值")

    def on_enum_index_changed(self, idx):
        if self._updating or idx < 0:
            return
        self.preserve_transform_and_set_attr(idx)

def show_space_switch_ui():
    global space_switch_win
    try:
        space_switch_win.close()
        space_switch_win.deleteLater()
    except:
        pass
    space_switch_win = SpaceSwitchUI()
    space_switch_win.show()
    return space_switch_win

if __name__ == "__main__":
    show_space_switch_ui()