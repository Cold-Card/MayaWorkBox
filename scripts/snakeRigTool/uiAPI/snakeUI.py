# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'snakeUI.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_snakeUI(object):
    def setupUi(self, snakeUI):
        if not snakeUI.objectName():
            snakeUI.setObjectName(u"snakeUI")
        snakeUI.resize(429, 527)
        self.actionImport_Demo_Snake = QAction(snakeUI)
        self.actionImport_Demo_Snake.setObjectName(u"actionImport_Demo_Snake")
        self.actionImportSnakeRig = QAction(snakeUI)
        self.actionImportSnakeRig.setObjectName(u"actionImportSnakeRig")
        self.actionReload_Plugin_Code = QAction(snakeUI)
        self.actionReload_Plugin_Code.setObjectName(u"actionReload_Plugin_Code")
        self.centralwidget = QWidget(snakeUI)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.frame = QFrame(self.centralwidget)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.Box)
        self.frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.frame)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.system_name_label = QLabel(self.frame)
        self.system_name_label.setObjectName(u"system_name_label")
        self.system_name_label.setMaximumSize(QSize(16777215, 35))
        font = QFont()
        font.setPointSize(11)
        self.system_name_label.setFont(font)

        self.horizontalLayout.addWidget(self.system_name_label)

        self.system_name_text = QLineEdit(self.frame)
        self.system_name_text.setObjectName(u"system_name_text")
        self.system_name_text.setMaximumSize(QSize(16777215, 35))
        self.system_name_text.setFont(font)

        self.horizontalLayout.addWidget(self.system_name_text)

        self.horizontalLayout.setStretch(0, 1)
        self.horizontalLayout.setStretch(1, 1)

        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.line = QFrame(self.frame)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_2.addWidget(self.line)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.meshName_text = QLineEdit(self.frame)
        self.meshName_text.setObjectName(u"meshName_text")
        self.meshName_text.setMaximumSize(QSize(16777215, 35))
        self.meshName_text.setFont(font)
        self.meshName_text.setReadOnly(True)

        self.horizontalLayout_2.addWidget(self.meshName_text)

        self.loadMesh_btn = QPushButton(self.frame)
        self.loadMesh_btn.setObjectName(u"loadMesh_btn")
        self.loadMesh_btn.setMaximumSize(QSize(16777215, 35))
        self.loadMesh_btn.setFont(font)

        self.horizontalLayout_2.addWidget(self.loadMesh_btn)

        self.horizontalLayout_2.setStretch(0, 1)
        self.horizontalLayout_2.setStretch(1, 1)

        self.verticalLayout_2.addLayout(self.horizontalLayout_2)

        self.line_2 = QFrame(self.frame)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.HLine)
        self.line_2.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_2.addWidget(self.line_2)

        self.build_guide_joint_btn = QPushButton(self.frame)
        self.build_guide_joint_btn.setObjectName(u"build_guide_joint_btn")
        self.build_guide_joint_btn.setMaximumSize(QSize(16777215, 35))
        self.build_guide_joint_btn.setFont(font)

        self.verticalLayout_2.addWidget(self.build_guide_joint_btn)

        self.line_10 = QFrame(self.frame)
        self.line_10.setObjectName(u"line_10")
        self.line_10.setFrameShape(QFrame.HLine)
        self.line_10.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_2.addWidget(self.line_10)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.label = QLabel(self.frame)
        self.label.setObjectName(u"label")
        self.label.setMaximumSize(QSize(16777215, 35))
        self.label.setFont(font)

        self.horizontalLayout_5.addWidget(self.label)

        self.path_cv_Slider = QSlider(self.frame)
        self.path_cv_Slider.setObjectName(u"path_cv_Slider")
        self.path_cv_Slider.setMaximumSize(QSize(16777215, 35))
        self.path_cv_Slider.setMinimum(4)
        self.path_cv_Slider.setMaximum(50)
        self.path_cv_Slider.setOrientation(Qt.Horizontal)

        self.horizontalLayout_5.addWidget(self.path_cv_Slider)

        self.path_cv_spinBox = QSpinBox(self.frame)
        self.path_cv_spinBox.setObjectName(u"path_cv_spinBox")
        self.path_cv_spinBox.setMaximumSize(QSize(16777215, 35))
        font1 = QFont()
        font1.setPointSize(12)
        self.path_cv_spinBox.setFont(font1)
        self.path_cv_spinBox.setMinimum(4)
        self.path_cv_spinBox.setMaximum(50)

        self.horizontalLayout_5.addWidget(self.path_cv_spinBox)

        self.horizontalLayout_5.setStretch(0, 1)
        self.horizontalLayout_5.setStretch(1, 1)
        self.horizontalLayout_5.setStretch(2, 1)

        self.verticalLayout_2.addLayout(self.horizontalLayout_5)

        self.line_7 = QFrame(self.frame)
        self.line_7.setObjectName(u"line_7")
        self.line_7.setFrameShape(QFrame.HLine)
        self.line_7.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_2.addWidget(self.line_7)

        self.set_guide_successed_btn = QPushButton(self.frame)
        self.set_guide_successed_btn.setObjectName(u"set_guide_successed_btn")
        self.set_guide_successed_btn.setMaximumSize(QSize(16777215, 35))
        self.set_guide_successed_btn.setFont(font)

        self.verticalLayout_2.addWidget(self.set_guide_successed_btn)

        self.line_9 = QFrame(self.frame)
        self.line_9.setObjectName(u"line_9")
        self.line_9.setFrameShape(QFrame.HLine)
        self.line_9.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_2.addWidget(self.line_9)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.body_neck_comboBox = QComboBox(self.frame)
        self.body_neck_comboBox.addItem("")
        self.body_neck_comboBox.addItem("")
        self.body_neck_comboBox.setObjectName(u"body_neck_comboBox")
        self.body_neck_comboBox.setMaximumSize(QSize(16777215, 35))
        self.body_neck_comboBox.setFont(font)

        self.horizontalLayout_4.addWidget(self.body_neck_comboBox)

        self.body_neck_Slider = QSlider(self.frame)
        self.body_neck_Slider.setObjectName(u"body_neck_Slider")
        self.body_neck_Slider.setMaximumSize(QSize(16777215, 35))
        self.body_neck_Slider.setMinimum(1)
        self.body_neck_Slider.setMaximum(100)
        self.body_neck_Slider.setOrientation(Qt.Horizontal)

        self.horizontalLayout_4.addWidget(self.body_neck_Slider)

        self.body_neck_spinBox = QSpinBox(self.frame)
        self.body_neck_spinBox.setObjectName(u"body_neck_spinBox")
        self.body_neck_spinBox.setMaximumSize(QSize(16777215, 35))
        self.body_neck_spinBox.setFont(font1)
        self.body_neck_spinBox.setMinimum(1)
        self.body_neck_spinBox.setMaximum(100)

        self.horizontalLayout_4.addWidget(self.body_neck_spinBox)

        self.horizontalLayout_4.setStretch(0, 1)
        self.horizontalLayout_4.setStretch(1, 1)
        self.horizontalLayout_4.setStretch(2, 1)

        self.verticalLayout_2.addLayout(self.horizontalLayout_4)

        self.line_8 = QFrame(self.frame)
        self.line_8.setObjectName(u"line_8")
        self.line_8.setFrameShape(QFrame.HLine)
        self.line_8.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_2.addWidget(self.line_8)

        self.buildRig_btn = QPushButton(self.frame)
        self.buildRig_btn.setObjectName(u"buildRig_btn")
        self.buildRig_btn.setMaximumSize(QSize(16777215, 35))
        self.buildRig_btn.setFont(font)

        self.verticalLayout_2.addWidget(self.buildRig_btn)


        self.verticalLayout.addWidget(self.frame)

        snakeUI.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(snakeUI)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 429, 26))
        self.menuMenu = QMenu(self.menubar)
        self.menuMenu.setObjectName(u"menuMenu")
        snakeUI.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(snakeUI)
        self.statusbar.setObjectName(u"statusbar")
        snakeUI.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuMenu.menuAction())
        self.menuMenu.addSeparator()
        self.menuMenu.addAction(self.actionImport_Demo_Snake)
        self.menuMenu.addSeparator()
        self.menuMenu.addAction(self.actionImportSnakeRig)
        self.menuMenu.addSeparator()
        self.menuMenu.addAction(self.actionReload_Plugin_Code)

        self.retranslateUi(snakeUI)

        QMetaObject.connectSlotsByName(snakeUI)
    # setupUi

    def retranslateUi(self, snakeUI):
        snakeUI.setWindowTitle(QCoreApplication.translate("snakeUI", u"Snake RigPlugin", None))
        self.actionImport_Demo_Snake.setText(QCoreApplication.translate("snakeUI", u"Import  Snake Mesh", None))
        self.actionImportSnakeRig.setText(QCoreApplication.translate("snakeUI", u"Import Snake Rig", None))
        self.actionReload_Plugin_Code.setText(QCoreApplication.translate("snakeUI", u"Reload Plugin Code", None))
        self.system_name_label.setText(QCoreApplication.translate("snakeUI", u"Rig  System  Name   :", None))
        self.loadMesh_btn.setText(QCoreApplication.translate("snakeUI", u"Load Mesh", None))
        self.build_guide_joint_btn.setText(QCoreApplication.translate("snakeUI", u"Build Guide Bone", None))
        self.label.setText(QCoreApplication.translate("snakeUI", u"Path CV Num :", None))
        self.set_guide_successed_btn.setText(QCoreApplication.translate("snakeUI", u"Set Guide Complete", None))
        self.body_neck_comboBox.setItemText(0, QCoreApplication.translate("snakeUI", u"Body", None))
        self.body_neck_comboBox.setItemText(1, QCoreApplication.translate("snakeUI", u"Neck", None))

        self.buildRig_btn.setText(QCoreApplication.translate("snakeUI", u"Build  Snake  System", None))
        self.menuMenu.setTitle(QCoreApplication.translate("snakeUI", u"Menu", None))
    # retranslateUi

