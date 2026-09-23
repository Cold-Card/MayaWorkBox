#coding=gbk
import sys
# 获取文件路径
import os
import inspect
import importlib
import maya.cmds as cmds

from pathlib import Path  # Maya 2022+ (Python 3) 内置，Maya 2020及以下也可用

# 获取当前文件路径并转为 Path 对象
current_file = Path(os.path.abspath(inspect.getsourcefile(lambda: 0)))

# 文件路径
file_path = current_file.parent

# 根路径：.parent 就相当于退一层，连续 .parent.parent.parent 退 3 层
root_path = current_file.parent.parent.parent.parent

# 版本号
maya_version = cmds.about(version=True)
# 库路径
library = root_path / maya_version

sys.path.append(file_path)

import new_rope_window
importlib.reload(new_rope_window)
from new_rope_window import *
window.show()
# stretch_condition = cmds.shadingNode('condition', asUtility=1)
        # cmds.connectAttr((self.prefix + 'TotalControl_Curve.stretch'), stretch_condition + '.firstTerm', f=1)
        # cmds.setAttr(stretch_condition + '.colorIfTrueR', 3)
        # cmds.setAttr(stretch_condition + '.colorIfFalseR', 4)
# cmds.connectAttr(stretch_condition + '.outColorR', value_condition + '.operation',f=1)
# 弹簧结算器
#ikSpringSolver