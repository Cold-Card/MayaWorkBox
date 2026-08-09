# -*- coding: utf-8 -*-
"""
LogicCompiler Package

Maya 节点逻辑编译器 - 将节点网络转换为可复用的 Python 代码。

Modules:
    core: 核心编译逻辑（可独立使用）
    ui: 用户界面
    main: 启动入口
    
Quick Start:
    # 启动 UI
    from LogicCompiler import ui
    ui.show()
    
    # 纯 API 使用
    from LogicCompiler.core import LogicCompiler
    compiler = LogicCompiler()
    code = compiler.compile(source, target, intermediates)
"""

__version__ = "2.0.0"
__author__ = "Logic Compiler Tool"

# === 兼容两种导入方式 ===
try:
    from .core import LogicCompiler
    from .ui import LogicCompilerUI
except ImportError:
    from core import LogicCompiler
    from ui import LogicCompilerUI

__all__ = ['LogicCompiler', 'LogicCompilerUI']
