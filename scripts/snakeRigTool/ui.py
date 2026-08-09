# -*- coding: utf-8 -*-
import os
from . import reload_mod
import maya.cmds as cmds
from .script import core
from .uiAPI import uiShowAPI, uiCmdAPI, snakeUI
from PySide2.QtWidgets import QMainWindow

class snakeToolUI(QMainWindow, snakeUI.Ui_snakeUI):
    def __init__(self, parent=uiShowAPI.get_maya_main_window()):
        super(snakeToolUI, self).__init__(parent)
        self.setupUi(self)
        self.linkCmd()

    def linkCmd(self):
        u'''
        链接命令
        '''
        self.loadMesh_btn.clicked.connect(lambda *args: self.loadMeshCmd())
        self.build_guide_joint_btn.clicked.connect(lambda *args: self.buildGuideJoint())
        self.path_cv_spinBox.valueChanged.connect(lambda *args: self.pathSpinBoxVccCmd())
        self.path_cv_Slider.valueChanged.connect(lambda *args: self.pathSliderVccCmd())
        self.body_neck_Slider.valueChanged.connect(lambda *args: self.insertSliderVccCmd())
        self.body_neck_spinBox.valueChanged.connect(lambda *args: self.insertSpinBoxVccCmd())
        self.set_guide_successed_btn.clicked.connect(lambda *args: self.guideCompleteCmd())
        self.buildRig_btn.clicked.connect(lambda *args: self.buildRig())

        self.actionImport_Demo_Snake.triggered.connect(lambda *args: self.importDemoMeshCmd())
        self.actionReload_Plugin_Code.triggered.connect(lambda *args: self.reloadPluginCodeCmd())
        self.actionImportSnakeRig.triggered.connect(lambda *args: self.importDemoRigFile())

    def loadMeshCmd(self):
        u'''
        加载模型命令
        '''
        sel = cmds.ls(sl=True)
        if not sel:
            return
        obj = sel[0]
        obj_shape_lst = core.getShpe(obj)
        if not obj_shape_lst or cmds.nodeType(obj_shape_lst[0]) != u"mesh":
            print(u"# Must Select PolyMesh")
            return
        self.meshName_text.setText(obj)

    def buildGuideJoint(self):
        u'''
        创建导航骨骼
        '''
        system_name = self.system_name_text.text()
        mesh = self.meshName_text.text()
        if not mesh or not system_name or not cmds.objExists(mesh):
            return
        uiCmdAPI.createNeckBodySE_joint(system_name, mesh)

    def pathSliderVccCmd(self):
        u'''
        路径曲线滑条数值变化时指行的命令
        '''
        value = self.path_cv_Slider.value()
        self.path_cv_spinBox.setValue(value)

    def pathSpinBoxVccCmd(self):
        u'''
        路径曲线spinbox数值变化时指行的命令
        '''
        value = self.path_cv_spinBox.value()
        self.path_cv_Slider.setValue(value)

    def insertSliderVccCmd(self):
        u'''
        插入骨骼滑条数值改变时执行的命令
        '''
        value = self.body_neck_Slider.value()
        self.body_neck_spinBox.setValue(value)

    def insertSpinBoxVccCmd(self):
        u'''
        插入骨骼spinBox数值改变时执行的命令
        '''
        value = self.body_neck_spinBox.value()
        self.body_neck_Slider.setValue(value)
        self.realTimeInsertJoint()

    def realTimeInsertJoint(self):
        u'''
        实时插入骨骼命令
        '''
        text = self.body_neck_comboBox.currentText()
        if text == "Body":
            is_body = True
        else:
            is_body = False
        insert_num = self.body_neck_spinBox.value()
        uiCmdAPI.realTimeCreateJoint(insert_num, is_body)

    def guideCompleteCmd(self):
        system_name = self.system_name_text.text()
        num = self.path_cv_spinBox.value()
        if not system_name:
            print(u"# Please Input System Name !!!")
            return
        new_num = num - 2
        uiCmdAPI.guideComplete(system_name, new_num)

    def buildRig(self):
        u'''
        创建绑定
        '''
        system_name = self.system_name_text.text()
        if not system_name:
            print(u"# Please Input System Name !!!")
            return
        uiCmdAPI.buildRigCmd(system_name)

    def importDemoMeshCmd(self):
        u'''
        导入demo蛇类模型命令
        '''
        now_path = __file__
        new_path = os.path.normpath(now_path).replace("\\", "/")
        demo_mesh_path = new_path.replace("/ui.py", "/demoFile/demoMesh.ma")
        if core.isEx("demoSnake"):
            return
        core.importFile(demo_mesh_path)

    def reloadPluginCodeCmd(self):
        u'''
        刷新蛇类插件所有模块
        '''
        now_path = __file__
        normal_path = os.path.normpath(now_path).replace("\\", "/")
        package_path = os.path.dirname(normal_path)
        reload_mod.reloadPackage(package_path)

    def importDemoRigFile(self):
        u'''
        导入绑定完成的绑定文件
        '''
        now_path = __file__
        new_path = os.path.normpath(now_path).replace("\\", "/")
        demo_rig_path = new_path.replace("/ui.py", "/demoFile/demoRig.ma")
        if core.isEx("s_Grp"):
            return
        core.importFile(demo_rig_path)

def show():
    uiShowAPI.deleteMayaSurplusUI(u"snakeUI")
    win = snakeToolUI()
    win.show()
