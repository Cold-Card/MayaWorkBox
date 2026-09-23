# -*- coding: utf 8 -*-
import os.path

import maya.cmds as cmds
from .toolkit import cmdAPI, rigModule
from .uiCore import uiAPI, featherUI, menu
from .reloadCode import reload_mod
from PySide2.QtWidgets import QMainWindow, QAction

class FeatherRig(QMainWindow, featherUI.Ui_birdFeatherTool):
    def __init__(self, parent=uiAPI.get_maya_main_window()):
        super(FeatherRig, self).__init__(parent)
        self.setupUi(self)

        self.linkCmd()

    def linkCmd(self):
        u'''
        链接命令
        '''
        self.buildFeatherBone_btn.clicked.connect(self.buildFeatherJointCmd)
        self.loadRootBone_btn.clicked.connect(self.loadRootBoneCmd)
        self.load_armBones_btn.clicked.connect(lambda *args: self.loadJntCmd(True))
        self.load_featherBones_btn.clicked.connect(lambda *args: self.loadJntCmd(False))
        self.autoParentBone_btn.clicked.connect(self.autoParentCmd)
        self.buildGuideBone_btn.clicked.connect(self.buildGuideJntCmd)
        self.boneNumber_slider.valueChanged.connect(self.sliderValuCcmd)
        self.boneNumber_spinBox.valueChanged.connect(self.spinBoxValuCcmd)
        self.buildRigSystem_btn.clicked.connect(self.buildRigCmd)

        clear_cmd_lst = [u"Clear All Items", u"Clear Selected"]
        arm_cmd_lst = [lambda *args:self.clearListItemCmd(True), lambda *args:self.clearSelectedItemsCmd(True)]
        feather_cmd_lst = [lambda *args:self.clearListItemCmd(False), lambda *args:self.clearSelectedItemsCmd(False)]
        menu.create_context_menu1(self.arm_list, clear_cmd_lst, arm_cmd_lst)
        menu.create_context_menu1(self.feather_list, clear_cmd_lst, feather_cmd_lst)

        self.actionImport_Demo_Joint.triggered.connect(lambda *args: self.importDemoJntCmd())
        self.actionImport_Demo_Mode.triggered.connect(lambda *args: self.importBirdModelCmd())
        self.actionReload_Code.triggered.connect(lambda *args: self.reloadCode())
    @property
    def getSide(self):
        u'''
        获取当前选项为 R还是 L
        '''
        return self.side_comboBox.currentText()

    @property
    def getComPareAxis(self):
        u'''
        获取需要比较的轴向
        '''
        return self.compare_comboBox.currentText()

    @property
    def getMirroState(self):
        u'''
        获取mirro的checkbox的状态，是否被点击
        '''
        return self.mirro_checkBox.isChecked()

    @property
    def rootBoneText(self):
        u'''
        获取根关节文本内容
        '''
        return self.rootBone_lineEdit.text()

    @property
    def getFeatherListAllText(self):
        u'''
        获取羽毛骨骼列表组件所有列表项文本
        '''
        items_text = []
        for index in range(self.feather_list.count()):
            item = self.feather_list.item(index)
            items_text.append(item.text())
        return items_text

    @property
    def getArmListAllText(self):
        u'''
        获取鸟类臂膀列表项所有的列表项文本
        '''
        items_text = []
        for index in range(self.arm_list.count()):
            item = self.arm_list.item(index)
            items_text.append(item.text())
        return items_text

    @property
    def getArmListSelectedText(self):
        u'''
        获取鸟类臂膀列表项已选中的列表项文本
        '''
        selected_items_text = []
        for item in self.arm_list.selectedItems():
            selected_items_text.append(item.text())
        return selected_items_text

    @property
    def getBoneNumber(self):
        u'''
        获取羽毛骨骼链的骨骼数量
        '''
        return self.boneNumber_spinBox.value()

    def buildFeatherJointCmd(self):
        u'''
        创建羽毛关节命令
        '''
        sel = cmds.ls(sl=True)
        if not sel:
            return
        mesh_lst = [m for m in sel if cmds.listRelatives(m, s=True) and cmds.nodeType(cmds.listRelatives(m, s=True)[0]) == u"mesh"]
        if not mesh_lst:
            return
        side = self.getSide
        axis = self.getComPareAxis
        cmdAPI.createJntByMesh(mesh_lst, axis, side)

    def loadRootBoneCmd(self):
        u'''
        加载根骨骼命令
        '''
        jnt_lst = cmds.ls(sl=True, type=u"joint")
        if not jnt_lst:
            return
        self.rootBone_lineEdit.setText(jnt_lst[0])

    def loadJntCmd(self, arm=True):
        u'''
        加载骨骼命令
        '''
        jnt_lst = cmds.ls(sl=True, type=u"joint")
        if not jnt_lst:
            return
        if arm == True:
            featherJointLst = self.getFeatherListAllText
            arm_jnt_lst = [i for i in jnt_lst if i not in featherJointLst]
            self.arm_list.clear()
            self.arm_list.addItems(arm_jnt_lst)
        else:
            armJointLst = self.getArmListAllText
            feather_jnt_lst = [i for i in jnt_lst if i not in armJointLst]
            self.feather_list.clear()
            self.feather_list.addItems(feather_jnt_lst)

    def autoParentCmd(self):
        u'''
        自动父子关系命令
        '''
        parentJntLst = self.getArmListSelectedText
        childJntLst = self.getFeatherListAllText
        if not parentJntLst or not childJntLst:
            return
        cmdAPI.autoParent(parentJntLst, childJntLst)

    def buildGuideJntCmd(self):
        u'''
        创建导航骨骼命令
        '''
        side = self.getSide
        armJntLst = self.getArmListAllText
        featherJntLst = self.getFeatherListAllText
        skinJntNum = self.getBoneNumber
        if not armJntLst or not featherJntLst:
            return
        rigModule.RigFeather(armJntLst, featherJntLst, skinJntNum, side).buildGuideJnt()

    def sliderValuCcmd(self):
        u'''
        滑条数值改变执行的命令
        '''
        value = self.boneNumber_slider.value()
        self.boneNumber_spinBox.setValue(value)

    def spinBoxValuCcmd(self):
        u'''
        spinbox数值改变执行的命令
        '''
        value = self.boneNumber_spinBox.value()
        self.boneNumber_slider.setValue(value)

    def buildRigCmd(self):
        u'''
        创建绑定系统的命令
        '''
        root = self.rootBoneText
        side = self.getSide
        armJntLst = self.getArmListAllText
        featherJntLst = self.getFeatherListAllText
        skinJntNum = self.getBoneNumber
        state = self.getMirroState
        if not armJntLst or not featherJntLst or not root:
            return
        rigModule.buildRig(root, armJntLst, featherJntLst, side, skinJntNum, state)

    def clearListItemCmd(self, arm=True):
        u'''
        清除列表项命令
        '''
        if arm==True:
            self.arm_list.clear()
        else:
            self.feather_list.clear()

    def clearSelectedItemsCmd(self, arm):
        u'''
        移除已选中的列表项
        '''
        if arm == True:
            selectedItems = self.arm_list.selectedItems()
            if not selectedItems:
                return
            for it in selectedItems:
                index = self.arm_list.row(it)
                self.arm_list.takeItem(index)
        else:
            selectedItems = self.feather_list.selectedItems()
            if not selectedItems:
                return
            for it in selectedItems:
                index = self.feather_list.row(it)
                self.feather_list.takeItem(index)

    def importDemoJntCmd(self):
        u'''
        导入案例骨骼命令
        '''
        if cmds.objExists(u"R_01_FEATHER_RIG_SYSTEM_DEMO_JOINT"):
            return
        now_path = os.path.normpath(__file__).replace("\\", "/")
        bone_path = now_path.replace("ui.py", "rigfile/bone.ma")
        cmdAPI.importFile(bone_path)

    def importBirdModelCmd(self):
        u'''
        导入案例模型命令
        '''
        if cmds.objExists(u"phoenix_G"):
            return
        now_path = os.path.normpath(__file__).replace("\\", "/")
        model_path = now_path.replace("ui.py", "rigfile/bird.ma")
        cmdAPI.importFile(model_path)

    def reloadCode(self):
        u'''
        刷新代码库
        '''
        now_path = os.path.normpath(__file__).replace("\\", "/")
        package_path = now_path.replace("/ui.py", "")
        reload_mod.reloadPackage(package_path)

def show():
    uiAPI.deleteMayaSurplusUI(u"birdFeatherTool")
    win = FeatherRig()
    win.show()