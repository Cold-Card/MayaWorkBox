# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'featherUI.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_birdFeatherTool(object):
    def setupUi(self, birdFeatherTool):
        if not birdFeatherTool.objectName():
            birdFeatherTool.setObjectName(u"birdFeatherTool")
        birdFeatherTool.resize(507, 601)
        self.actionImport_Demo_Joint = QAction(birdFeatherTool)
        self.actionImport_Demo_Joint.setObjectName(u"actionImport_Demo_Joint")
        self.actionImport_Demo_Mode = QAction(birdFeatherTool)
        self.actionImport_Demo_Mode.setObjectName(u"actionImport_Demo_Mode")
        self.actionReload_Code = QAction(birdFeatherTool)
        self.actionReload_Code.setObjectName(u"actionReload_Code")
        self.centralwidget = QWidget(birdFeatherTool)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.mainFrame = QFrame(self.centralwidget)
        self.mainFrame.setObjectName(u"mainFrame")
        self.mainFrame.setFrameShape(QFrame.Box)
        self.mainFrame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.mainFrame)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.side_label = QLabel(self.mainFrame)
        self.side_label.setObjectName(u"side_label")
        font = QFont()
        font.setPointSize(9)
        self.side_label.setFont(font)

        self.horizontalLayout.addWidget(self.side_label)

        self.side_comboBox = QComboBox(self.mainFrame)
        self.side_comboBox.addItem("")
        self.side_comboBox.addItem("")
        self.side_comboBox.setObjectName(u"side_comboBox")
        font1 = QFont()
        font1.setPointSize(10)
        self.side_comboBox.setFont(font1)

        self.horizontalLayout.addWidget(self.side_comboBox)

        self.mirro_checkBox = QCheckBox(self.mainFrame)
        self.mirro_checkBox.setObjectName(u"mirro_checkBox")
        self.mirro_checkBox.setFont(font)
        self.mirro_checkBox.setChecked(True)

        self.horizontalLayout.addWidget(self.mirro_checkBox)

        self.horizontalLayout.setStretch(0, 1)
        self.horizontalLayout.setStretch(1, 1)
        self.horizontalLayout.setStretch(2, 1)

        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.line_4 = QFrame(self.mainFrame)
        self.line_4.setObjectName(u"line_4")
        self.line_4.setFrameShape(QFrame.HLine)
        self.line_4.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_2.addWidget(self.line_4)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.compare_label = QLabel(self.mainFrame)
        self.compare_label.setObjectName(u"compare_label")
        self.compare_label.setFont(font)

        self.horizontalLayout_2.addWidget(self.compare_label)

        self.compare_comboBox = QComboBox(self.mainFrame)
        self.compare_comboBox.addItem("")
        self.compare_comboBox.addItem("")
        self.compare_comboBox.addItem("")
        self.compare_comboBox.setObjectName(u"compare_comboBox")
        self.compare_comboBox.setFont(font1)

        self.horizontalLayout_2.addWidget(self.compare_comboBox)

        self.buildFeatherBone_btn = QPushButton(self.mainFrame)
        self.buildFeatherBone_btn.setObjectName(u"buildFeatherBone_btn")
        self.buildFeatherBone_btn.setFont(font)

        self.horizontalLayout_2.addWidget(self.buildFeatherBone_btn)

        self.horizontalLayout_2.setStretch(0, 1)
        self.horizontalLayout_2.setStretch(1, 1)
        self.horizontalLayout_2.setStretch(2, 1)

        self.verticalLayout_2.addLayout(self.horizontalLayout_2)

        self.line_11 = QFrame(self.mainFrame)
        self.line_11.setObjectName(u"line_11")
        self.line_11.setFrameShape(QFrame.HLine)
        self.line_11.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_2.addWidget(self.line_11)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.rootBone_lineEdit = QLineEdit(self.mainFrame)
        self.rootBone_lineEdit.setObjectName(u"rootBone_lineEdit")
        self.rootBone_lineEdit.setMaximumSize(QSize(16777215, 30))
        self.rootBone_lineEdit.setFont(font)

        self.horizontalLayout_3.addWidget(self.rootBone_lineEdit)

        self.loadRootBone_btn = QPushButton(self.mainFrame)
        self.loadRootBone_btn.setObjectName(u"loadRootBone_btn")
        self.loadRootBone_btn.setFont(font)

        self.horizontalLayout_3.addWidget(self.loadRootBone_btn)

        self.horizontalLayout_3.setStretch(0, 1)
        self.horizontalLayout_3.setStretch(1, 1)

        self.verticalLayout_2.addLayout(self.horizontalLayout_3)

        self.line = QFrame(self.mainFrame)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_2.addWidget(self.line)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.arm_list = QListWidget(self.mainFrame)
        self.arm_list.setObjectName(u"arm_list")
        self.arm_list.setFont(font1)
        self.arm_list.setSelectionMode(QAbstractItemView.MultiSelection)

        self.horizontalLayout_7.addWidget(self.arm_list)

        self.feather_list = QListWidget(self.mainFrame)
        self.feather_list.setObjectName(u"feather_list")
        self.feather_list.setFont(font1)
        self.feather_list.setSelectionMode(QAbstractItemView.MultiSelection)

        self.horizontalLayout_7.addWidget(self.feather_list)


        self.verticalLayout_2.addLayout(self.horizontalLayout_7)

        self.line_2 = QFrame(self.mainFrame)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.HLine)
        self.line_2.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_2.addWidget(self.line_2)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.load_armBones_btn = QPushButton(self.mainFrame)
        self.load_armBones_btn.setObjectName(u"load_armBones_btn")
        self.load_armBones_btn.setFont(font)

        self.horizontalLayout_6.addWidget(self.load_armBones_btn)

        self.load_featherBones_btn = QPushButton(self.mainFrame)
        self.load_featherBones_btn.setObjectName(u"load_featherBones_btn")
        self.load_featherBones_btn.setFont(font)

        self.horizontalLayout_6.addWidget(self.load_featherBones_btn)


        self.verticalLayout_2.addLayout(self.horizontalLayout_6)

        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.autoParentBone_btn = QPushButton(self.mainFrame)
        self.autoParentBone_btn.setObjectName(u"autoParentBone_btn")
        self.autoParentBone_btn.setFont(font)

        self.horizontalLayout_8.addWidget(self.autoParentBone_btn)

        self.buildGuideBone_btn = QPushButton(self.mainFrame)
        self.buildGuideBone_btn.setObjectName(u"buildGuideBone_btn")
        self.buildGuideBone_btn.setFont(font)

        self.horizontalLayout_8.addWidget(self.buildGuideBone_btn)


        self.verticalLayout_2.addLayout(self.horizontalLayout_8)

        self.line_3 = QFrame(self.mainFrame)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setFrameShape(QFrame.HLine)
        self.line_3.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_2.addWidget(self.line_3)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.boneNumber_label = QLabel(self.mainFrame)
        self.boneNumber_label.setObjectName(u"boneNumber_label")
        self.boneNumber_label.setFont(font)

        self.horizontalLayout_5.addWidget(self.boneNumber_label)

        self.boneNumber_slider = QSlider(self.mainFrame)
        self.boneNumber_slider.setObjectName(u"boneNumber_slider")
        self.boneNumber_slider.setFont(font)
        self.boneNumber_slider.setMinimum(5)
        self.boneNumber_slider.setMaximum(20)
        self.boneNumber_slider.setOrientation(Qt.Horizontal)

        self.horizontalLayout_5.addWidget(self.boneNumber_slider)

        self.boneNumber_spinBox = QSpinBox(self.mainFrame)
        self.boneNumber_spinBox.setObjectName(u"boneNumber_spinBox")
        self.boneNumber_spinBox.setFont(font)
        self.boneNumber_spinBox.setMinimum(5)
        self.boneNumber_spinBox.setMaximum(20)

        self.horizontalLayout_5.addWidget(self.boneNumber_spinBox)

        self.horizontalLayout_5.setStretch(0, 1)
        self.horizontalLayout_5.setStretch(1, 3)
        self.horizontalLayout_5.setStretch(2, 2)

        self.verticalLayout_2.addLayout(self.horizontalLayout_5)

        self.line_5 = QFrame(self.mainFrame)
        self.line_5.setObjectName(u"line_5")
        self.line_5.setFrameShape(QFrame.HLine)
        self.line_5.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_2.addWidget(self.line_5)

        self.buildRigSystem_btn = QPushButton(self.mainFrame)
        self.buildRigSystem_btn.setObjectName(u"buildRigSystem_btn")
        self.buildRigSystem_btn.setFont(font)

        self.verticalLayout_2.addWidget(self.buildRigSystem_btn)


        self.verticalLayout.addWidget(self.mainFrame)

        birdFeatherTool.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(birdFeatherTool)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 507, 26))
        self.menuMenu = QMenu(self.menubar)
        self.menuMenu.setObjectName(u"menuMenu")
        birdFeatherTool.setMenuBar(self.menubar)

        self.menubar.addAction(self.menuMenu.menuAction())
        self.menuMenu.addSeparator()
        self.menuMenu.addAction(self.actionImport_Demo_Joint)
        self.menuMenu.addSeparator()
        self.menuMenu.addAction(self.actionImport_Demo_Mode)
        self.menuMenu.addSeparator()
        self.menuMenu.addAction(self.actionReload_Code)
        self.menuMenu.addSeparator()

        self.retranslateUi(birdFeatherTool)

        QMetaObject.connectSlotsByName(birdFeatherTool)
    # setupUi

    def retranslateUi(self, birdFeatherTool):
        birdFeatherTool.setWindowTitle(QCoreApplication.translate("birdFeatherTool", u"Feather Rig System", None))
        self.actionImport_Demo_Joint.setText(QCoreApplication.translate("birdFeatherTool", u"Import Demo Joint", None))
        self.actionImport_Demo_Mode.setText(QCoreApplication.translate("birdFeatherTool", u"Import Demo Model", None))
        self.actionReload_Code.setText(QCoreApplication.translate("birdFeatherTool", u"Reload Code", None))
        self.side_label.setText(QCoreApplication.translate("birdFeatherTool", u"Rig System Side   :", None))
        self.side_comboBox.setItemText(0, QCoreApplication.translate("birdFeatherTool", u"R", None))
        self.side_comboBox.setItemText(1, QCoreApplication.translate("birdFeatherTool", u"L", None))

        self.mirro_checkBox.setText(QCoreApplication.translate("birdFeatherTool", u"Mirro Rig System", None))
        self.compare_label.setText(QCoreApplication.translate("birdFeatherTool", u"Compare   Axis    :", None))
        self.compare_comboBox.setItemText(0, QCoreApplication.translate("birdFeatherTool", u"Z", None))
        self.compare_comboBox.setItemText(1, QCoreApplication.translate("birdFeatherTool", u"Y", None))
        self.compare_comboBox.setItemText(2, QCoreApplication.translate("birdFeatherTool", u"X", None))

        self.buildFeatherBone_btn.setText(QCoreApplication.translate("birdFeatherTool", u"Build Feather Bone", None))
        self.loadRootBone_btn.setText(QCoreApplication.translate("birdFeatherTool", u"Load Root Bone", None))
        self.load_armBones_btn.setText(QCoreApplication.translate("birdFeatherTool", u"Load Arm Bone", None))
        self.load_featherBones_btn.setText(QCoreApplication.translate("birdFeatherTool", u"Load Feather Bone", None))
        self.autoParentBone_btn.setText(QCoreApplication.translate("birdFeatherTool", u"Auto Parent Bone", None))
        self.buildGuideBone_btn.setText(QCoreApplication.translate("birdFeatherTool", u"Build Guide Bone", None))
        self.boneNumber_label.setText(QCoreApplication.translate("birdFeatherTool", u"Bone Number :", None))
        self.buildRigSystem_btn.setText(QCoreApplication.translate("birdFeatherTool", u"Build Rig System", None))
        self.menuMenu.setTitle(QCoreApplication.translate("birdFeatherTool", u"Menu", None))
    # retranslateUi

