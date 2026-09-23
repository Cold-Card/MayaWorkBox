# -*- coding:utf-8 -*-

import os
import maya.cmds as cmds
import maya.mel as mel

# ————————————————————————————————————————————————————————————————————————————————
# global

# 獲取腳本路徑
try:
    TH_TOOLS_FILE_PATH = os.path.dirname(__file__)
except:
    TH_TOOLS_FILE_PATH = r'D:\PythonPj\TH_RIG_TOOLS\ThRigTools'
finally:
    TH_TOOLS_FILE_PATH = TH_TOOLS_FILE_PATH.replace('\\', '/')


# ————————————————————————————————————————————————————————————————————————————————
# func

def thAddMenusF():
    iconPath = f'{TH_TOOLS_FILE_PATH}/thRigToolsFiles/files/icons/icon.png'
    command = f'''\
import os
import sys
import maya.cmds as cmds
#
TH_TOOLS_FILE_PATH = '{TH_TOOLS_FILE_PATH}'
# 加入路徑
if not os.path.exists(TH_TOOLS_FILE_PATH):
    raise IOError(f'Cannot find: {{TH_TOOLS_FILE_PATH}}')
#
if TH_TOOLS_FILE_PATH not in sys.path:
    sys.path.insert(0, TH_TOOLS_FILE_PATH)
# 透過 Maya 的 MQtUtil 或內建指令來確保舊視窗存在時將其安全刪除，此處改用預防 GC 閃退的持久化清理
if hasattr(cmds, "thMainUiInstance"):
    try:
        cmds.thMainUiInstance.close()
        cmds.thMainUiInstance.deleteLater()
    except:
        pass
#
if hasattr(cmds, "thLogoUiInstance"):
    try:
        cmds.thLogoUiInstance.close()
        cmds.thLogoUiInstance.deleteLater()
    except:
        pass
# 在刪除模組前，先清理 QApplication 中的翻譯器
if 'thRigToolsFiles.rig' in sys.modules:
    try:
        sys.modules['thRigToolsFiles.rig'].ThLanguage.setLanguageF('zh_TW')
    except Exception as e:
        print(f"清理語言失敗: {{e}}")
# 強制清除模組
for mod in list(sys.modules.keys()):
    if mod.startswith('thRigToolsFiles.rig'):
        sys.modules.pop(mod)
# 重新載入
import thRigToolsFiles.rig
# 顯示 UI
thRigToolsFiles.rig.ThInitUi.initDataF()
# 將視窗實例動態註冊到 cmds 模組中，等同於 Blender 的 bpy.types 作法
cmds.thMainUiInstance = thRigToolsFiles.rig.ThUiMain()
cmds.thMainUiInstance.show()
#
cmds.thLogoUiInstance = thRigToolsFiles.rig.ThUiLogoShow()
cmds.thLogoUiInstance.show()
'''
    shelf = mel.eval('$gShelfTopLevel=$gShelfTopLevel')
    parent = cmds.tabLayout(shelf, query=True, selectTab=True)
    cmds.shelfButton(
        command=command,
        annotation='TH RIG TOOLS',
        sourceType='Python',
        imageOverlayLabel='',
        image=iconPath,
        image1=iconPath,
        parent=parent)


def onMayaDroppedPythonFile(*args, **kwargs):
    """僅從 Maya 2017 Update 3 開始支持此功能"""
    thAddMenusF()


# ————————————————————————————————————————————————————————————————————————————————
# apply
if __name__ == '__main__':
    thAddMenusF()