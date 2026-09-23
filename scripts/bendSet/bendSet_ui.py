# bendSet_ui_styled_final.py
import maya.cmds as cmds
import pymel.core as pm
from PySide2 import QtWidgets, QtCore, QtGui
from shiboken2 import wrapInstance
import maya.OpenMayaUI as omui

try:
    from . import bendSet as bs
except ImportError:
    cmds.warning("请确保 bendSet.py 已导入或放置在脚本路径中")
    raise

def get_maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)

def apply_style(widget):
    # ========== 优化后的全局样式表 ==========
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

class BendSetUI(QtWidgets.QDialog):
    def __init__(self, parent=get_maya_main_window()):
        super(BendSetUI, self).__init__(parent)
        self.setWindowTitle("Bend System Tool")
        #self.setMinimumSize(600, 750)  # 增加最小尺寸，确保内容完整
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        apply_style(self)  # 应用优化后的样式表

        self.remap_AngleWeight_list = []

        self.init_ui()
        self.load_defaults()

    def init_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(3, 3, 3, 3)

        tabs = QtWidgets.QTabWidget()
        main_layout.addWidget(tabs)

        # 主标签页（卷曲 + 权重）
        tab_main = QtWidgets.QWidget()
        tabs.addTab(tab_main, "创建")
        self.setup_main_tab(tab_main)

        # Follow Parent 标签页
        tab_follow = QtWidgets.QWidget()
        tabs.addTab(tab_follow, "跟随驱动")
        self.setup_follow_tab(tab_follow)

    # ---------- 辅助控件 ----------
    def create_list_widget(self, label, tooltip=""):
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        label_widget = QtWidgets.QLabel(label)
        label_widget.setMinimumWidth(70)
        layout.addWidget(label_widget,0)

        text_edit = QtWidgets.QLineEdit()
        text_edit.setStyleSheet("QLineEdit {background-color: #2E2E2E; border: 1px solid #2E2E2E;}")
        text_edit.setReadOnly(True)
        text_edit.setToolTip(tooltip)
        layout.addWidget(text_edit,4)

        load_btn = QtWidgets.QPushButton("载入")
        load_btn.setMinimumWidth(50)
        load_btn.setProperty("secondary", True)
        layout.addWidget(load_btn,1)

        layout.text_edit = text_edit
        layout.load_btn = load_btn
        return layout

    def create_line_edit(self, label, default=""):
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        label_widget = QtWidgets.QLabel(label)
        label_widget.setMinimumWidth(70)
        layout.addWidget(label_widget)
        edit = QtWidgets.QLineEdit(default)
        layout.addWidget(edit)
        layout.edit = edit
        return layout

    def create_checkbox_group(self, label, options, default_checked=None):
        group = QtWidgets.QGroupBox(label)
        layout = QtWidgets.QHBoxLayout(group)
        layout.setSpacing(12)
        layout.setContentsMargins(8, 8, 8, 8)
        checkboxes = []
        for opt in options:
            cb = QtWidgets.QCheckBox(opt)
            if default_checked and opt in default_checked:
                cb.setChecked(True)
            layout.addWidget(cb)
            checkboxes.append(cb)
        group.checkboxes = checkboxes
        return group

    def get_checked_values(self, checkbox_group):
        return [cb.text() for cb in checkbox_group.checkboxes if cb.isChecked()]

    # ---------- 主标签页 ----------
    def setup_main_tab(self, parent):
        layout = QtWidgets.QVBoxLayout(parent)
        layout.setSpacing(12)

        # 卷曲系统参数
        group_bend = QtWidgets.QGroupBox("卷曲系统")
        bend_layout = QtWidgets.QVBoxLayout(group_bend)
        bend_layout.setSpacing(8)

        self.bend_list_widget = self.create_list_widget("卷曲列表", "被驱动卷曲的对象")
        bend_layout.addLayout(self.bend_list_widget)
        self.bend_list_widget.load_btn.clicked.connect(lambda: self.load_selection(self.bend_list_widget.text_edit,"被驱动卷曲的对象"))

        self.ctrl_list_widget = self.create_list_widget("控制列表", "对应的控制器对象")
        bend_layout.addLayout(self.ctrl_list_widget)
        self.ctrl_list_widget.load_btn.clicked.connect(lambda: self.load_selection(self.ctrl_list_widget.text_edit,"对应的控制器对象"))

        self.prefix_widget = self.create_line_edit("前缀", "")
        bend_layout.addLayout(self.prefix_widget)

        self.bend_ctrl_name_widget = self.create_line_edit("控制器名称", "bend_ctrl")
        bend_layout.addLayout(self.bend_ctrl_name_widget)

        self.aixs_group = self.create_checkbox_group("卷曲轴向", ["X", "Y", "Z"], default_checked=["Z", "Y", "X"])
        self.aixs_group.setFixedHeight(55)
        bend_layout.addWidget(self.aixs_group)

        btn_create = QtWidgets.QPushButton("创建卷曲系统")
        btn_create.setProperty("primary", True)
        btn_create.setStyleSheet("QPushButton {font-size: 14px;}")
        btn_create.setFixedHeight(36)
        btn_create.clicked.connect(self.create_bend_system)
        bend_layout.addWidget(btn_create)

        layout.addWidget(group_bend)

        # Remap 列表
        remap_group = QtWidgets.QGroupBox("Remap 节点列表")
        remap_layout = QtWidgets.QVBoxLayout(remap_group)
        remap_layout.setSpacing(8)

        btn_row = QtWidgets.QHBoxLayout()
        btn_row.setSpacing(8)
        load_sel_btn = QtWidgets.QPushButton("载入")
        #load_sel_btn.setFixedWidth(50)
        load_sel_btn.setProperty("secondary", True)
        load_sel_btn.clicked.connect(self.load_remap_from_selection)
        btn_row.addWidget(load_sel_btn)

        clear_btn = QtWidgets.QPushButton("清空列表")
        clear_btn.setProperty("secondary", True)
        clear_btn.clicked.connect(self.clear_remap_list)
        btn_row.addWidget(clear_btn)

        load_scene_btn = QtWidgets.QPushButton("从场景搜索")
        load_scene_btn.setProperty("secondary", True)
        load_scene_btn.clicked.connect(self.load_remap_from_scene)
        btn_row.addWidget(load_scene_btn)
        #btn_row.addStretch()
        remap_layout.addLayout(btn_row)

        self.remap_list_widget = QtWidgets.QListWidget()
        #self.remap_list_widget.setMinimumHeight(150)
        self.remap_list_widget.setAlternatingRowColors(True)
        self.remap_list_widget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        remap_layout.addWidget(self.remap_list_widget)

        layout.addWidget(remap_group)
        #layout.addStretch()        

        # 角度权重控制参数
        group_weight = QtWidgets.QGroupBox("角度权重控制")
        weight_layout = QtWidgets.QVBoxLayout(group_weight)
        weight_layout.setSpacing(8)

        ctrl_num_layout = QtWidgets.QHBoxLayout()
        ctrl_num_layout.addWidget(QtWidgets.QLabel("控制点数量:"))
        self.ctrl_num_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.ctrl_num_slider.setMinimum(2)
        self.ctrl_num_slider.setMaximum(20)
        self.ctrl_num_slider.setValue(5)
        self.ctrl_num_slider.setTickInterval(1)
        self.ctrl_num_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        ctrl_num_layout.addWidget(self.ctrl_num_slider)

        self.ctrl_num_spinbox = QtWidgets.QSpinBox()
        self.ctrl_num_spinbox.setMinimum(2)
        self.ctrl_num_spinbox.setMaximum(20)
        self.ctrl_num_spinbox.setValue(5)
        self.ctrl_num_spinbox.setFixedWidth(40)
        ctrl_num_layout.addWidget(self.ctrl_num_spinbox)

        self.ctrl_num_slider.valueChanged.connect(self.ctrl_num_spinbox.setValue)
        self.ctrl_num_spinbox.valueChanged.connect(self.ctrl_num_slider.setValue)

        weight_layout.addLayout(ctrl_num_layout)

        btn_create_weight = QtWidgets.QPushButton("创建角度权重控制")
        btn_create_weight.setProperty("primary", True)
        btn_create_weight.setStyleSheet("QPushButton {font-size: 14px;}")
        btn_create_weight.setFixedHeight(36)
        btn_create_weight.clicked.connect(self.create_angle_weight_ctrl)
        weight_layout.addWidget(btn_create_weight)

        layout.addWidget(group_weight)


    # ---------- Follow Parent 标签页 ----------
    def setup_follow_tab(self, parent):
        layout = QtWidgets.QVBoxLayout(parent)
        layout.setSpacing(12)

        # 共用控件
        self.driver_list_widget = self.create_list_widget("驱动列表", "驱动变换的对象")
        layout.addLayout(self.driver_list_widget)
        self.driver_list_widget.load_btn.clicked.connect(lambda: self.load_selection(self.driver_list_widget.text_edit,"驱动变换的对象"))

        self.driven_list_widget = self.create_list_widget("被驱动列表", "被驱动变换的对象")
        layout.addLayout(self.driven_list_widget)
        self.driven_list_widget.load_btn.clicked.connect(lambda: self.load_selection(self.driven_list_widget.text_edit,"被驱动变换的对象"))

        self.follow_aixs_group = self.create_checkbox_group("驱动轴", ["t", "r"], default_checked=["t", "r"])
        layout.addWidget(self.follow_aixs_group)

        follow_type_group = QtWidgets.QGroupBox("跟随类型")
        follow_type_layout = QtWidgets.QVBoxLayout(follow_type_group)
        follow_type_layout.setSpacing(8)

        self.follow_type_combo = QtWidgets.QComboBox()
        self.follow_type_combo.setStyleSheet("QComboBox {font-weight: bold; font-size: 11px;}")
        #self.follow_type_combo.setFixedWidth(200)
        self.follow_type_combo.addItems(["单层卷曲", "双层卷曲"])
        self.follow_type_combo.currentIndexChanged.connect(self.on_follow_type_changed)
        follow_type_layout.addWidget(self.follow_type_combo)
        
        self.follow_stack = QtWidgets.QStackedWidget()
        self.follow_stack.setFrameShape(QtWidgets.QFrame.NoFrame)
        follow_type_layout.addWidget(self.follow_stack)
        #follow_type_layout.addStretch()
        layout.addWidget(follow_type_group)

        # one
        page_one = QtWidgets.QWidget()
        one_layout = QtWidgets.QVBoxLayout(page_one)
        one_layout.setSpacing(8)
        self.bend_list_one_widget = self.create_list_widget("卷曲列表", "提供 followParent 属性的对象")
        one_layout.addLayout(self.bend_list_one_widget)
        self.bend_list_one_widget.load_btn.clicked.connect(lambda: self.load_selection(self.bend_list_one_widget.text_edit,"提供 followParent 属性的对象"))
        self.follow_attr_widget = self.create_line_edit("属性名", "followParent")
        one_layout.addLayout(self.follow_attr_widget)
        #one_layout.addStretch()
        self.follow_stack.addWidget(page_one)

        # two
        page_two = QtWidgets.QWidget()
        two_layout = QtWidgets.QVBoxLayout(page_two)
        two_layout.setSpacing(8)
        self.a_bend_list_widget = self.create_list_widget("A-卷曲列表", "提供 followParent 属性的对象")
        two_layout.addLayout(self.a_bend_list_widget)
        self.a_bend_list_widget.load_btn.clicked.connect(lambda: self.load_selection(self.a_bend_list_widget.text_edit,"提供 followParent 属性的对象"))
        self.b_bend_list_widget = self.create_list_widget("B-卷曲列表", "提供 followParent 属性的对象")
        two_layout.addLayout(self.b_bend_list_widget)
        self.b_bend_list_widget.load_btn.clicked.connect(lambda: self.load_selection(self.b_bend_list_widget.text_edit,"提供 followParent 属性的对象"))
        self.a_follow_attr_widget = self.create_line_edit("A-属性", "body_followParent")
        two_layout.addLayout(self.a_follow_attr_widget)
        self.b_follow_attr_widget = self.create_line_edit("B-属性", "tail_followParent")
        two_layout.addLayout(self.b_follow_attr_widget)
        #two_layout.addStretch()
        self.follow_stack.addWidget(page_two)

        btn_connect = QtWidgets.QPushButton("执行连接")
        btn_connect.setProperty("primary", True)
        btn_connect.setStyleSheet("QPushButton {font-size: 14px;}")
        btn_connect.setFixedHeight(36)
        btn_connect.clicked.connect(self.connect_follow_parent)
        layout.addWidget(btn_connect)

        layout.addStretch()
        self.on_follow_type_changed(0)

    def on_follow_type_changed(self, index):
        self.follow_stack.setCurrentIndex(index)

    # ---------- 辅助方法 ----------
    def load_selection(self, line_edit, tooltip=""):
        sel = pm.ls(sl=True)
        if sel:
            names = [str(obj) for obj in sel]
            line_edit.setText(", ".join(names))
            out = "\n...\n{} 个对象未显示".format(len(names)-20) if len(names) > 20 else ""
            tooltip_detail = "{}\n\n{} 个对象\n\n{}{}".format(tooltip,len(names), "\n".join(names[:20]),out)
            line_edit.setToolTip(tooltip_detail)
        else:
            line_edit.clear()
            line_edit.setToolTip(tooltip)

    def get_list_from_text(self, line_edit):
        text = line_edit.text().strip()
        if not text:
            return []
        return [item.strip() for item in text.split(",") if item.strip()]

    def load_defaults(self):
        pass

    # ---------- Remap 操作 ----------
    def load_remap_from_selection(self):
        sel = pm.ls(sl=True)
        if not sel:
            cmds.warning("请先选中要载入的 remap 节点")
            return
        remap_nodes = []
        for obj in sel:
            obj_node = pm.PyNode(obj)
            if obj_node.type() == 'remapValue' or str(obj).endswith('_bend_remap_AngleWeight'):
                remap_nodes.append(str(obj))
        if not remap_nodes:
            cmds.warning("选中对象中没有找到 remap 节点")
            return
        self.remap_AngleWeight_list = remap_nodes
        self.update_remap_list()
        cmds.confirmDialog(title="加载成功", message=f"载入 {len(remap_nodes)} 个 remap 节点", button=["确定"])

    def load_remap_from_scene(self):
        prefix = bs.prefix_logic(self.prefix_widget.edit.text())
        all_remaps = pm.ls(type='remapValue')
        matched = []
        for node in all_remaps:
            name = str(node)
            if name.endswith('_bend_remap_AngleWeight'):
                if name.startswith(prefix):
                    matched.append(name)
        if matched:
            self.remap_AngleWeight_list = matched
            self.update_remap_list()
            cmds.confirmDialog(title="加载成功", message=f"找到 {len(matched)} 个 remap 节点", button=["确定"])
        else:
            cmds.warning("未找到匹配的 remap 节点")

    def clear_remap_list(self):
        self.remap_AngleWeight_list = []
        self.update_remap_list()

    def update_remap_list(self):
        self.remap_list_widget.clear()
        for item in self.remap_AngleWeight_list:
            self.remap_list_widget.addItem(str(item))

    # ---------- 执行功能 ----------
    def create_bend_system(self):
        bend_list = self.get_list_from_text(self.bend_list_widget.text_edit)
        ctrl_list = self.get_list_from_text(self.ctrl_list_widget.text_edit)
        prefix = self.prefix_widget.edit.text().strip()
        bend_ctrl_name = self.bend_ctrl_name_widget.edit.text().strip()
        aixs = self.get_checked_values(self.aixs_group)

        if not bend_list or not ctrl_list:
            cmds.warning("请确保 Bend列表 和 控制列表 不为空")
            return
        if len(bend_list) != len(ctrl_list):
            cmds.warning("卷曲列表与控制列表数量必须一致")
            return
        if not aixs:
            cmds.warning("至少选择一个旋转轴")
            return
        if not bend_ctrl_name:
            cmds.warning("控制器名称不能为空")
            return

        try:
            bend_ctrl = bs.get_bend_ctrl(bend_ctrl_name, prefix)
            remap_list = bs.create_bend_system(
                bend_list, ctrl_list, bend_ctrl, prefix, aixs,
                self.remap_AngleWeight_list
            )
        except Exception as exc:
            cmds.warning("创建卷曲系统失败: {}".format(exc))
            return

        self.remap_AngleWeight_list = remap_list
        self.update_remap_list()
        cmds.confirmDialog(title="完成", message="卷曲系统创建完成！", button=["确定"])

    def create_angle_weight_ctrl(self):
        prefix = bs.prefix_logic(self.prefix_widget.edit.text())
        bend_ctrl_name = self.bend_ctrl_name_widget.edit.text()
        bend_ctrl = bs.get_bend_ctrl(bend_ctrl_name, prefix)
        if not pm.objExists(bend_ctrl):
            cmds.warning(f"未找到控制器 {bend_ctrl}，请先创建卷曲系统或指定正确名称")
            return
        ctrl_num = self.ctrl_num_spinbox.value()
        if not self.remap_AngleWeight_list:
            cmds.warning("当前 remap 列表为空，请先创建卷曲系统或从场景加载")
            return
        bs.create_AngleWeight_ctrl(bend_ctrl, ctrl_num, self.remap_AngleWeight_list, prefix)
        cmds.confirmDialog(title="完成", message="角度权重控制创建完成！", button=["确定"])

    def connect_follow_parent(self):
        follow_type = self.follow_type_combo.currentIndex()
        driver_list = self.get_list_from_text(self.driver_list_widget.text_edit)
        driven_list = self.get_list_from_text(self.driven_list_widget.text_edit)
        aixs = self.get_checked_values(self.follow_aixs_group)

        if not driver_list or not driven_list:
            cmds.warning("驱动列表和被驱动列表不能为空")
            return
        if len(driver_list) != len(driven_list):
            cmds.warning("驱动列表与被驱动列表数量必须一致")
            return
        if not aixs:
            cmds.warning("至少选择一个驱动轴")
            return

        try:
            if follow_type == 0:
                bend_list = self.get_list_from_text(self.bend_list_one_widget.text_edit)
                follow_attr = self.follow_attr_widget.edit.text().strip()
                if not bend_list:
                    cmds.warning("卷曲列表不能为空")
                    return
                if len(bend_list) != len(driver_list):
                    cmds.warning("卷曲、驱动、被驱动 列表数量必须一致")
                    return
                if not follow_attr:
                    cmds.warning("属性名不能为空")
                    return
                bs.connection_one_followParent(
                    bend_list, driver_list, driven_list, follow_attr, aixs
                )
            else:
                a_bend_list = self.get_list_from_text(self.a_bend_list_widget.text_edit)
                b_bend_list = self.get_list_from_text(self.b_bend_list_widget.text_edit)
                a_attr = self.a_follow_attr_widget.edit.text().strip()
                b_attr = self.b_follow_attr_widget.edit.text().strip()
                if not a_bend_list or not b_bend_list:
                    cmds.warning("A-卷曲列表和B-卷曲列表不能为空")
                    return
                if len(a_bend_list) != len(driver_list) or len(b_bend_list) != len(driver_list):
                    cmds.warning("A-卷曲、B-卷曲、驱动、被驱动 列表数量必须一致")
                    return
                if not a_attr or not b_attr:
                    cmds.warning("A/B 属性名不能为空")
                    return
                bs.connection_two_followParent(
                    a_bend_list, b_bend_list, driver_list, driven_list,
                    a_attr, b_attr, aixs
                )
        except Exception as exc:
            cmds.warning("跟随驱动连接失败: {}".format(exc))
            return

        cmds.confirmDialog(title="完成", message="跟随驱动连接完成！", button=["确定"])

# ---------- 启动 ----------
def show_ui():
    global bend_set_ui
    try:
        if bend_set_ui is not None:
            bend_set_ui.close()
            bend_set_ui.deleteLater()
    except (NameError, RuntimeError):
        pass
    bend_set_ui = BendSetUI()
    bend_set_ui.show()

if __name__ == "__main__":
    show_ui()