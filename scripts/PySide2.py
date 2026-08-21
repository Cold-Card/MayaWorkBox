import sys
import importlib
from types import ModuleType

def install_full_compatibility():
    """
    让 Maya 2026 完全兼容 PySide2 和 shiboken2
    """
    
    # --- 1. 处理 shiboken2 ---
    try:
        import shiboken6
        sys.modules['shiboken2'] = shiboken6
        # 如果代码里用 import shiboken2; shiboken2.wrapInstance
        # 这样设置能确保属性一致
    except ImportError:
        print("Warning: shiboken6 not found.")

    # --- 2. 处理 PySide2 顶层模块 ---
    if 'PySide2' not in sys.modules:
        pyside2_mock = ModuleType('PySide2')
        sys.modules['PySide2'] = pyside2_mock

    # --- 3. 映射所有常用的子模块 ---
    # 这样 from PySide2 import QtUiTools 这种写法就能生效
    sub_modules = [
        'QtCore', 'QtWidgets', 'QtGui', 'QtUiTools', 
        'QtNetwork', 'QtSvg', 'QtOpenGL', 'QtPrintSupport'
    ]

    import PySide6
    for mod_name in sub_modules:
        try:
            # 导入 PySide6 的模块
            p6_mod = importlib.import_module(f'PySide6.{mod_name}')
            # 映射到 sys.modules
            sys.modules[f'PySide2.{mod_name}'] = p6_mod
            # 同时挂载到 PySide2 对象上
            setattr(sys.modules['PySide2'], mod_name, p6_mod)
        except ImportError:
            continue

    # --- 4. 关键类补丁 (QtWidgets <-> QtGui) ---
    # Qt6 把 QAction/QShortcut 等移到了 QtGui，这里把它们塞回 QtWidgets
    from PySide6 import QtGui, QtWidgets, QtCore
    moved_classes = [
        'QAction', 'QActionGroup', 'QShortcut', 'QUndoCommand', 
        'QUndoStack', 'QUndoGroup', 'QUndoView', 'QFileSystemModel'
    ]
    for cls_name in moved_classes:
        if hasattr(QtGui, cls_name):
            setattr(QtWidgets, cls_name, getattr(QtGui, cls_name))

    # --- 5. 修复 exec_() 方法 ---
    # PySide6 主要是 exec()，PySide2 主要是 exec_()
    for cls in [QtWidgets.QDialog, QtWidgets.QApplication, QtWidgets.QMenu, 
                QtCore.QCoreApplication, QtCore.QThread, QtCore.QEventLoop]:
        if hasattr(cls, 'exec') and not hasattr(cls, 'exec_'):
            cls.exec_ = cls.exec

    # --- 6. 修复枚举值 (Qt.AlignLeft 等) ---
    def promote_enums(target_obj):
        for attr_name in dir(target_obj):
            if attr_name.startswith('_'): continue
            try:
                attr = getattr(target_obj, attr_name)
                # 检查是否是枚举类
                if isinstance(attr, type) and 'PySide6' in str(attr):
                    for enum_field in dir(attr):
                        if not enum_field.startswith('_'):
                            if not hasattr(target_obj, enum_field):
                                setattr(target_obj, enum_field, getattr(attr, enum_field))
            except:
                continue

    promote_enums(QtCore.Qt)
    promote_enums(QtWidgets.QFrame)

    print("--- Maya 2026 PySide2 & shiboken2 Compatibility Ready ---")

# 立即执行
install_full_compatibility()