# -*- coding: utf-8 -*-
import maya.cmds as cmds
from functools import partial

# === 兼容两种导入方式 ===
try:
    from .core import LogicCompiler
except ImportError:
    from core import LogicCompiler


class LogicCompilerUI:
    """
    Maya 节点逻辑编译器的 UI 类。
    
    职责：
        1. 构建和管理 Maya UI 界面
        2. 处理用户交互事件
        3. 调用 LogicCompiler 核心类完成验证和编译
        4. 支持直接测试运行生成的代码
    """
    
    WINDOW_NAME = "NodeLogicCompiler_Pro"
    TITLE = u"节点逻辑编译器_V1.0"
    SIZE = (650, 850)
    
    def __init__(self):
        """初始化 UI 并创建编译器实例。"""
        # 原始节点（用于生成代码）
        self.source_nodes = []
        self.target_nodes = []
        
        # 测试节点（用于运行代码）
        self.test_source_nodes = []
        self.test_target_nodes = []
        
        # 生成的代码（缓存）
        self._generated_code = ""
        
        # 核心编译器实例
        self.compiler = LogicCompiler()
        
        # UI 控件引用
        self.window = None
        self.source_list = None
        self.target_list = None
        self.scroll_field = None
        self.test_source_list = None
        self.test_target_list = None
        
        self._build_ui()

    def _build_ui(self):
        """构建工具的 UI 界面。"""
        if cmds.window(self.WINDOW_NAME, exists=True):
            cmds.deleteUI(self.WINDOW_NAME)
            
        self.window = cmds.window(self.WINDOW_NAME, title=self.TITLE, widthHeight=self.SIZE)
        
        main_form = cmds.formLayout(numberOfDivisions=100, parent=self.window)
        
        # 使用 scrollLayout 包裹所有内容
        scroll = cmds.scrollLayout(childResizable=True)
        
        main_col = cmds.columnLayout(adjustableColumn=True, rowSpacing=5)
        
        # --- Part 1: 定义输入/输出端 ---
        self._build_input_section(main_col)
        
        # --- Part 2: 中间节点与生成 ---
        self._build_intermediate_section(main_col)
        
        # --- Part 3: 输出代码区 ---
        self._build_output_section(main_col)
        
        # --- Part 4: 测试运行区 (新增) ---
        self._build_test_section(main_col)

        cmds.setParent(main_form)

        # --- Attachments ---
        cmds.formLayout(main_form, edit=True,
                        attachForm=[
                            (scroll, 'top', 0), 
                            (scroll, 'bottom', 0),
                            (scroll, 'left', 0), 
                            (scroll, 'right', 0)
                        ])

        cmds.showWindow(self.window)

    def _build_input_section(self, parent):
        """构建输入端定义区域 - 支持多节点。"""
        cmds.frameLayout(
            label="1. 定义输入/输出端:",
            collapsable=True, 
            collapse=False,
            marginWidth=10, 
            marginHeight=10,
            parent=parent
        )
        
        main_col = cmds.columnLayout(adjustableColumn=True, rowSpacing=8)
        
        # === Source 区域 ===
        cmds.text(label="驱动端:", align="left", font="boldLabelFont")
        
        source_row = cmds.rowLayout(numberOfColumns=2, adjustableColumn=1, columnAttach=[(2, 'right', 0)])
        
        self.source_list = cmds.textScrollList(
            height=60, 
            allowMultiSelection=True,
            deleteKeyCommand=lambda: self._on_remove_from_list('source')
        )
        
        btn_col = cmds.columnLayout(rowSpacing=2)
        cmds.button(label="+ Add", width=60, backgroundColor=(0.4, 0.6, 0.4), 
                    command=partial(self._on_add_nodes, 'source'))
        cmds.button(label="- Remove", width=60, backgroundColor=(0.6, 0.4, 0.4),
                    command=partial(self._on_remove_from_list, 'source'))
        cmds.button(label="Clear", width=60, 
                    command=partial(self._on_clear_list, 'source'))
        cmds.setParent('..')
        
        cmds.setParent('..')
        
        cmds.separator(height=10, style='single')
        
        # === Target 区域 ===
        cmds.text(label="被驱动端:", align="left", font="boldLabelFont")
        
        target_row = cmds.rowLayout(numberOfColumns=2, adjustableColumn=1, columnAttach=[(2, 'right', 0)])
        
        self.target_list = cmds.textScrollList(
            height=60, 
            allowMultiSelection=True,
            deleteKeyCommand=lambda: self._on_remove_from_list('target')
        )
        
        btn_col2 = cmds.columnLayout(rowSpacing=2)
        cmds.button(label="+ Add", width=60, backgroundColor=(0.4, 0.6, 0.4),
                    command=partial(self._on_add_nodes, 'target'))
        cmds.button(label="- Remove", width=60, backgroundColor=(0.6, 0.4, 0.4),
                    command=partial(self._on_remove_from_list, 'target'))
        cmds.button(label="Clear", width=60,
                    command=partial(self._on_clear_list, 'target'))
        cmds.setParent('..')
        
        cmds.setParent('..')
        cmds.setParent('..')
        cmds.setParent('..')

    def _build_intermediate_section(self, parent):
        """构建中间节点选择区域。"""
        cmds.frameLayout(
            label="2. 中间节点与生成",
            collapsable=True,
            collapse=False,
            marginWidth=10, 
            marginHeight=10, 
            parent=parent
        )
        cmds.columnLayout(adjustableColumn=True)
        cmds.text(
            label="框选所有中间节点后点击生成按钮", 
            align="center", 
            height=30, 
            backgroundColor=(0.25, 0.25, 0.25)
        )
        cmds.separator(h=5, style='none')
        
        cmds.button(
            label="生成 Python 脚本",
            height=40, 
            backgroundColor=(0.3, 0.6, 0.4), 
            command=self._on_generate
        )
        cmds.setParent('..') 
        cmds.setParent('..')

    def _build_output_section(self, parent):
        """构建输出代码区域。"""
        cmds.frameLayout(
            label="3. 输出代码",
            collapsable=True,
            collapse=False,
            marginWidth=5, 
            marginHeight=5,
            parent=parent
        )
        self.scroll_field = cmds.scrollField(
            editable=True, 
            wordWrap=False, 
            font="fixedWidthFont",
            height=200
        )
        cmds.setParent('..')

    def _build_test_section(self, parent):
        """构建测试运行区域（新功能）。"""
        cmds.frameLayout(
            label="4. 测试运行",
            collapsable=True,
            collapse=False,
            marginWidth=10, 
            marginHeight=10,
            parent=parent,
            backgroundColor=(0.2, 0.25, 0.3)
        )
        
        main_col = cmds.columnLayout(adjustableColumn=True, rowSpacing=8)
        
        cmds.text(
            label="指定新的 Source/Target 节点来测试生成的代码\n(无需手动复制粘贴代码)", 
            align="center", 
            height=35,
            backgroundColor=(0.15, 0.2, 0.25)
        )
        
        cmds.separator(height=5, style='none')
        
        # === 测试 Source ===
        cmds.text(label="新驱动端:", align="left", font="boldLabelFont")
        
        test_src_row = cmds.rowLayout(numberOfColumns=2, adjustableColumn=1, columnAttach=[(2, 'right', 0)])
        
        self.test_source_list = cmds.textScrollList(
            height=50, 
            allowMultiSelection=True,
            deleteKeyCommand=lambda: self._on_remove_from_list('test_source')
        )
        
        btn_col = cmds.columnLayout(rowSpacing=2)
        cmds.button(label="+ Add", width=60, backgroundColor=(0.3, 0.5, 0.6), 
                    command=partial(self._on_add_nodes, 'test_source'))
        cmds.button(label="Clear", width=60, 
                    command=partial(self._on_clear_list, 'test_source'))
        cmds.setParent('..')
        
        cmds.setParent('..')
        
        cmds.separator(height=5, style='single')
        
        # === 测试 Target ===
        cmds.text(label="新被驱动端:", align="left", font="boldLabelFont")
        
        test_tgt_row = cmds.rowLayout(numberOfColumns=2, adjustableColumn=1, columnAttach=[(2, 'right', 0)])
        
        self.test_target_list = cmds.textScrollList(
            height=50, 
            allowMultiSelection=True,
            deleteKeyCommand=lambda: self._on_remove_from_list('test_target')
        )
        
        btn_col2 = cmds.columnLayout(rowSpacing=2)
        cmds.button(label="+ Add", width=60, backgroundColor=(0.3, 0.5, 0.6),
                    command=partial(self._on_add_nodes, 'test_target'))
        cmds.button(label="Clear", width=60,
                    command=partial(self._on_clear_list, 'test_target'))
        cmds.setParent('..')
        
        cmds.setParent('..')
        
        cmds.separator(height=10, style='none')
        
        # === 运行按钮 ===
        cmds.button(
            label="▶ 运行测试 (Execute Code)", 
            height=45, 
            backgroundColor=(0.6, 0.4, 0.2),
            command=self._on_run_test
        )
        
        cmds.separator(height=5, style='none')
        
        # === 快捷操作 ===
        cmds.rowLayout(numberOfColumns=2, adjustableColumn=2, columnAttach=[(1, 'left', 0), (2, 'right', 0)])
        cmds.button(
            label="复制原始节点到测试区", 
            width=200,
            command=self._on_copy_to_test
        )
        cmds.button(
            label="清空测试区", 
            width=100,
            command=self._on_clear_test_all
        )
        cmds.setParent('..')
        
        cmds.setParent('..')
        cmds.setParent('..')

    # ==================== 事件处理器 ====================
    
    def _on_add_nodes(self, node_type, *args):
        """添加当前选中的节点到列表。"""
        sel = cmds.ls(selection=True)
        if not sel:
            cmds.warning("请先选择节点。")
            return
        
        # 根据类型选择对应的列表
        list_map = {
            'source': (self.source_nodes, self.source_list),
            'target': (self.target_nodes, self.target_list),
            'test_source': (self.test_source_nodes, self.test_source_list),
            'test_target': (self.test_target_nodes, self.test_target_list),
        }
        
        node_list, list_widget = list_map[node_type]
        
        added_count = 0
        for node in sel:
            if node not in node_list:
                node_list.append(node)
                cmds.textScrollList(list_widget, edit=True, append=node)
                added_count += 1
        
        if added_count > 0:
            cmds.inViewMessage(
                amg=f'<span style="color:#88FF88;">添加了 {added_count} 个节点</span>',
                pos='midCenter',
                fade=True
            )

    def _on_remove_from_list(self, node_type, *args):
        """从列表中移除选中的节点。"""
        list_map = {
            'source': (self.source_nodes, self.source_list),
            'target': (self.target_nodes, self.target_list),
            'test_source': (self.test_source_nodes, self.test_source_list),
            'test_target': (self.test_target_nodes, self.test_target_list),
        }
        
        node_list, list_widget = list_map[node_type]
        selected = cmds.textScrollList(list_widget, query=True, selectItem=True) or []
        
        for item in selected:
            if item in node_list:
                node_list.remove(item)
            cmds.textScrollList(list_widget, edit=True, removeItem=item)

    def _on_clear_list(self, node_type, *args):
        """清空节点列表。"""
        list_map = {
            'source': (self.source_nodes, self.source_list),
            'target': (self.target_nodes, self.target_list),
            'test_source': (self.test_source_nodes, self.test_source_list),
            'test_target': (self.test_target_nodes, self.test_target_list),
        }
        
        if node_type in list_map:
            node_list, list_widget = list_map[node_type]
            node_list.clear()
            cmds.textScrollList(list_widget, edit=True, removeAll=True)

    def _on_generate(self, *args):
        """生成按钮点击事件：验证网络并编译代码。"""
        if not self.source_nodes:
            cmds.warning("请至少添加一个 Source 节点。")
            return
        if not self.target_nodes:
            cmds.warning("请至少添加一个 Target 节点。")
            return
        
        all_endpoints = set(self.source_nodes + self.target_nodes)
        intermediates = cmds.ls(selection=True) or []
        intermediates = [n for n in intermediates if n not in all_endpoints]
        
        missing_nodes = self.compiler.validate_network(
            self.source_nodes, 
            self.target_nodes, 
            intermediates
        )
        
        if missing_nodes:
            if not self._show_missing_warning(missing_nodes):
                return

        code = self.compiler.compile(
            self.source_nodes, 
            self.target_nodes, 
            intermediates
        )
        
        # 缓存生成的代码
        self._generated_code = code
        
        cmds.scrollField(self.scroll_field, edit=True, text=code)
        
        msg = f'<span style="color:#88FF88;">成功生成代码！'
        msg += f'{len(self.source_nodes)} Source(s), '
        msg += f'{len(self.target_nodes)} Target(s), '
        msg += f'{len(intermediates)} 中间节点</span>'
        cmds.inViewMessage(amg=msg, pos='midCenter', fade=True)

    def _on_run_test(self, *args):
        """运行测试按钮点击事件：执行生成的代码。"""
        # 获取当前代码（可能被用户编辑过）
        code = cmds.scrollField(self.scroll_field, query=True, text=True)
        
        if not code or not code.strip():
            cmds.warning("请先生成代码。")
            return
        
        # 验证测试节点数量是否匹配
        num_original_sources = len(self.source_nodes)
        num_original_targets = len(self.target_nodes)
        num_test_sources = len(self.test_source_nodes)
        num_test_targets = len(self.test_target_nodes)
        
        if num_test_sources != num_original_sources:
            cmds.warning(f"测试 Source 数量 ({num_test_sources}) 与原始数量 ({num_original_sources}) 不匹配！")
            return
        
        if num_test_targets != num_original_targets:
            cmds.warning(f"测试 Target 数量 ({num_test_targets}) 与原始数量 ({num_original_targets}) 不匹配！")
            return
        
        # 构建函数调用参数
        if num_test_sources == 1 and num_test_targets == 1:
            call_args = f"'{self.test_source_nodes[0]}', '{self.test_target_nodes[0]}'"
        else:
            args_list = []
            for src in self.test_source_nodes:
                args_list.append(f"'{src}'")
            for tgt in self.test_target_nodes:
                args_list.append(f"'{tgt}'")
            call_args = ", ".join(args_list)
        
        # 构建完整的执行代码
        exec_code = code + f"\n\n# === 测试调用 ===\nbuild_connection_logic({call_args})"
        
        # 执行代码
        try:
            exec(exec_code, {'__builtins__': __builtins__})
            cmds.inViewMessage(
                amg='<span style="color:#88FF88;">✓ 测试执行成功！</span>',
                pos='midCenter',
                fade=True
            )
        except Exception as e:
            cmds.warning(f"执行失败: {str(e)}")
            cmds.confirmDialog(
                title='执行错误',
                message=f"代码执行失败:\n\n{str(e)}",
                button=['确定'],
                icon='critical'
            )

    def _on_copy_to_test(self, *args):
        """将原始 Source/Target 复制到测试区。"""
        # 清空测试区
        self.test_source_nodes = list(self.source_nodes)
        self.test_target_nodes = list(self.target_nodes)
        
        # 更新 UI
        cmds.textScrollList(self.test_source_list, edit=True, removeAll=True)
        cmds.textScrollList(self.test_target_list, edit=True, removeAll=True)
        
        for node in self.test_source_nodes:
            cmds.textScrollList(self.test_source_list, edit=True, append=node)
        for node in self.test_target_nodes:
            cmds.textScrollList(self.test_target_list, edit=True, append=node)
        
        cmds.inViewMessage(
            amg='<span style="color:#88FFFF;">已复制节点到测试区</span>',
            pos='midCenter',
            fade=True
        )

    def _on_clear_test_all(self, *args):
        """清空所有测试节点。"""
        self._on_clear_list('test_source')
        self._on_clear_list('test_target')

    def _show_missing_warning(self, missing_nodes):
        """显示漏选节点警告对话框。"""
        msg = "检测到由于漏选节点导致的逻辑断裂:\n\n"
        msg += "\n".join(missing_nodes[:10])
        if len(missing_nodes) > 10: 
            msg += f"\n... (共 {len(missing_nodes)} 个)"
        msg += "\n\n是否继续生成？"
        
        result = cmds.confirmDialog(
            title='断链警告', 
            message=msg, 
            button=['继续生成', '取消'], 
            defaultButton='取消', 
            icon='warning'
        )
        return result == '继续生成'


def show():
    """显示 LogicCompiler UI 的便捷函数。"""
    return LogicCompilerUI()
