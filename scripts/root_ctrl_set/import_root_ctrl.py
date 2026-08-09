# -*- coding: utf-8 -*-
# author: wangruilong
# date: 20250630

import os
import maya.cmds as cmds

ctrl_path = os.path.normpath(os.path.join(
    os.path.dirname(__file__),'root_ctrl.ma'))
    
def import_root_ctrl():
    cmds.file(ctrl_path, i=True, type='mayaAscii', ignoreVersion=True)

if __name__ == '__main__':
    import_root_ctrl()