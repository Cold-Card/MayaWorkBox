# -*- coding: utf-8 -*-

import os
import maya.mel as mel
import maya.cmds as cmds

now_path = __file__
normal_path = os.path.normpath(now_path).replace("\\", "/")
now_package = os.path.dirname(now_path)

iconPth = now_path.replace("install.py", "/uiAPI/icon/snake.png")
upper_path = os.path.dirname(normal_path)
toolName = "snakeRigTool"

command = '''
import os
import sys

if not os.path.exists(r'{path}'):
    raise IOError(r'The source path "{path}" does not exist!')

if r'{path}' not in sys.path:
    sys.path.insert(0, r'{path}')
    
from snakeRigTool import ui

ui.show()
'''.format(path=upper_path)

shelf = mel.eval('$gShelfTopLevel=$gShelfTopLevel')
parent = cmds.tabLayout(shelf, query=True, selectTab=True)
cmds.shelfButton(
        command=command,
        annotation=toolName,
        sourceType='Python',
        image=iconPth,
        image1=iconPth,
        parent=parent)


print("# install successful !!!")
