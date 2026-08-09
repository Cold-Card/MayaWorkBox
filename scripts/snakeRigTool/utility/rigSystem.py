# -*- coding: utf 8 -*-
import maya.cmds as cmds
from . import rigData, constValue
from ..script import cmdCore, core, pyCore

class SnakeRigSystem:
    u'''
    蛇类绑定系统
    '''
    def __init__(self, system_name, body_joint_lst, neck_joint_lst, path_curve):
        self.system_name = system_name
        self.body_joint_lst = body_joint_lst
        self.neck_joint_lst = neck_joint_lst
        self.path_curve = path_curve

        rigData.NodeCls.path_curve = self.path_curve

        rigData.GroupCls.mainGroup = "{}_MainGroup".format(self.system_name)
        rigData.GroupCls.noMoveGroup = "{}_NoMoveGroup".format(self.system_name)
        rigData.GroupCls.locJointGroup = "{}_LocJointGroup".format(self.system_name)

        self.group_lst = [rigData.GroupCls.mainGroup, rigData.GroupCls.noMoveGroup,
                          rigData.GroupCls.locJointGroup]
        cmdCore.createOnlyOneGrp(self.group_lst)

        core.propertyParent(rigData.GroupCls.noMoveGroup, rigData.GroupCls.mainGroup)
        core.propertyParent(rigData.GroupCls.locJointGroup, rigData.GroupCls.mainGroup)


    def step_01(self):
        u'''
        第一步, 创建身体定位器，将身体与脖子关节作为子级 p 给 定位器
        '''
        bn_loc_name = "{}_BnLoc".format(self.system_name)
        if not core.isEx(bn_loc_name):
            cmds.spaceLocator(n=bn_loc_name)
        if bn_loc_name not in core.getParent(self.body_joint_lst[0]):
            core.matchPos(self.body_joint_lst[0], bn_loc_name)
        core.propertyParent(self.body_joint_lst[0], bn_loc_name)
        core.propertyParent(self.neck_joint_lst[0], bn_loc_name)
        core.propertyParent(bn_loc_name, rigData.GroupCls.locJointGroup)

        rigData.NodeCls.bnLocNode = bn_loc_name

    def createMainCtrl(self):
        u'''
        创建主控制器, 创建脖子fk控制器
        '''
        main_ctrl = "{}_MainCtrl".format(self.system_name)
        main_ctrl_grp = cmdCore.createMainCtrl(main_ctrl, 8)
        core.propertyParent(main_ctrl_grp, rigData.GroupCls.mainGroup)
        bnLocA = "{}A".format(rigData.NodeCls.bnLocNode)
        if not core.isEx(bnLocA):
            cmds.spaceLocator(n=bnLocA)
        core.matchPos(rigData.NodeCls.bnLocNode, bnLocA)
        core.propertyParent(bnLocA, main_ctrl)
        cmds.parentConstraint(bnLocA, rigData.NodeCls.bnLocNode, mo=True)
        cmds.scaleConstraint(bnLocA, rigData.NodeCls.bnLocNode, mo=True)

        neck_fk_ctrl_data = cmdCore.createFkCtrl(self.neck_joint_lst, constValue.ValueCls.fk_ctrl_size)
        core.propertyParent(neck_fk_ctrl_data["conGrpA"][0], main_ctrl)

        rigData.NodeCls.bnLocNodeA = bnLocA
        rigData.OtherData.main_ctrl = main_ctrl
        rigData.OtherData.neck_fk_con_lst = neck_fk_ctrl_data["con"]
        rigData.OtherData.neck_fk_conGrp_lst = neck_fk_ctrl_data["conGrp"]
        rigData.OtherData.neck_fk_conGrpA_lst = neck_fk_ctrl_data["conGrpA"]

    def createBodySplineIk(self):
        u'''
        创建身体样条ik绑定
        '''
        bodySplineIkCurve = "{}_BodySplineIkCurve".format(self.system_name)
        if not core.isEx(bodySplineIkCurve):
            core.createCurveByObjLst(self.body_joint_lst, 3, bodySplineIkCurve)
        core.propertyParent(bodySplineIkCurve, rigData.GroupCls.noMoveGroup)
        bodySplineIkCurve_copy = "{}_BodyWaveCurve".format(self.system_name)
        if not core.isEx(bodySplineIkCurve_copy):
            copy_curve = core.noNamesakeDuplicate(bodySplineIkCurve)
            cmds.rename(copy_curve, bodySplineIkCurve_copy)

        splineIkJointList = core.createBoneChainByOldBoneLst(self.body_joint_lst, self.system_name, "SplineIkJoint")
        core.propertyParent(splineIkJointList[0], rigData.NodeCls.bnLocNode)

        ik_name = "{}_BodySplineIkHandle".format(self.system_name)
        if not core.isEx(ik_name):
            cmdCore.createSplineIk(splineIkJointList[0], splineIkJointList[-1], bodySplineIkCurve, ik_name)
        core.propertyParent(ik_name, rigData.GroupCls.noMoveGroup)

        cluster_lst = core.createCurveCluster(bodySplineIkCurve, False, show=False)

        splineIkCtrlData = cmdCore.createIkCtrl(cluster_lst, constValue.ValueCls.ik_ctrl_size, [0, 0, 1])

        [core.matchPos(jnt, grpA, 2) for grpA, jnt in zip(splineIkCtrlData["conGrpALst"], self.body_joint_lst)]

        splineIkCtrlMainGroup = "{}_SplineIkCtrlGroup".format(self.system_name)
        if not core.isEx(splineIkCtrlMainGroup):
            cmdCore.createOnlyOneGrp([splineIkCtrlMainGroup])
        core.propertyParent(splineIkCtrlMainGroup, rigData.OtherData.main_ctrl)
        [core.propertyParent(grpA, splineIkCtrlMainGroup) for grpA in splineIkCtrlData["conGrpALst"]]

        core.propertyParent(rigData.OtherData.neck_fk_conGrpA_lst[0], splineIkCtrlData["conLst"][0])

        rigData.NodeCls.body_ik = ik_name
        rigData.NodeCls.bodySplineIkCurve = bodySplineIkCurve
        rigData.NodeCls.bodyWaveCurve = bodySplineIkCurve_copy
        rigData.JointLstCls.splineJointLst = splineIkJointList
        rigData.OtherData.splineIkMainCtrlGroup = splineIkCtrlMainGroup
        rigData.OtherData.body_ik_con_lst = splineIkCtrlData["conLst"]
        rigData.OtherData.body_ik_conGrp_lst = splineIkCtrlData["conGrpLst"]
        rigData.OtherData.body_ik_conGrpA_lst = splineIkCtrlData["conGrpALst"]

    def bodyStretchRig(self):
        u'''
        身体样条ik骨骼拉伸绑定
        '''
        core.concealObjects([rigData.NodeCls.bnLocNode, rigData.NodeCls.bnLocNodeA])
        cmdCore.stretchRig(rigData.OtherData.main_ctrl,
                           rigData.NodeCls.bodySplineIkCurve,
                           rigData.JointLstCls.splineJointLst)

    def bodySinExpRig(self):
        u'''
        身体正弦波浪表达式绑定
        '''
        for splineIkCtrl in rigData.OtherData.body_ik_con_lst:
            if not core.hasAttr(splineIkCtrl, "widthRG"):
                cmds.addAttr(splineIkCtrl, ln="widthRG", at=u"double", dv=1, k=True)
        speed_attr = "{}.speed".format(rigData.OtherData.main_ctrl)
        width_attr = "{}.width".format(rigData.OtherData.main_ctrl)
        go_attr = "{}.go".format(rigData.OtherData.main_ctrl)
        delay_attr = "{}.delay".format(rigData.OtherData.main_ctrl)
        addWidth_attr = "{}.addWidth".format(rigData.OtherData.main_ctrl)
        exp = core.sinExpContent(rigData.OtherData.body_ik_conGrp_lst, "tz", rigData.OtherData.body_ik_con_lst,
                           "widthRG", speed_attr, width_attr, go_attr, delay_attr, addWidth_attr)
        core.createEXP(exp, "{}_BodySinExp".format(self.system_name))

    def bodyFkCtrlRig(self):
        u'''
        身体fk控制器绑定
        '''
        
        fk_bn_ctrl_list = core.createBoneChainByOldBoneLst(self.body_joint_lst, self.system_name, "FkCtrl")
        fk_ctrl_shape_lst = cmdCore.jointToFkCtrl(fk_bn_ctrl_list, constValue.ValueCls.fk_ctrl_size)

        rigData.OtherData.body_fk_bn_ctrl_list = fk_bn_ctrl_list
        rigData.OtherData.fk_ctrl_shape_lst = fk_ctrl_shape_lst

    def bodyBindJoint(self):
        u'''
        身体绑定关节制作
        '''
        
        body_bind_list = core.createBoneChainByOldBoneLst(self.body_joint_lst, self.system_name, "BodyBindJoint")
        core.oneToOneParent(rigData.OtherData.body_fk_bn_ctrl_list, body_bind_list)

        rigData.JointLstCls.bodyBindJointLst = body_bind_list

    def bodyRotRig(self):
        u'''
        身体整体旋转绑定 (身体旋转 A 层骨骼)
        '''
        
        body_rot_joint_listA = core.createBoneChainByOldBoneLst(self.body_joint_lst, self.system_name, "BodyRotJointA")

        core.conAttr([rigData.OtherData.main_ctrl], body_rot_joint_listA, "rotx", "rx")
        core.conAttr([rigData.OtherData.main_ctrl], body_rot_joint_listA, "roty", "ry")
        core.conAttr([rigData.OtherData.main_ctrl], body_rot_joint_listA, "rotz", "rz")

        core.eachParent(body_rot_joint_listA, rigData.OtherData.body_fk_bn_ctrl_list)

        rigData.JointLstCls.bodyRotJointLstA = body_rot_joint_listA

    def tailBendExpRig(self):
        u'''
        尾巴卷曲表达式绑定, 并且处理了好层级关系
        '''
        body_rot_joint_listB = core.createBoneChainByOldBoneLst(self.body_joint_lst, self.system_name, "BodyRotJointB")
        tailBendLocalAttrLst = []
        for fk_bn in rigData.OtherData.body_fk_bn_ctrl_list:
            if not core.hasAttr(fk_bn, "tailBend"):
                cmds.addAttr(fk_bn, ln="tailBend", at=u"double", dv=1, k=True)
            tailBendLocalAttrLst.append("{}.tailBend".format(fk_bn))
        tailBendLocalAttrLst.reverse()

        tail_joint_lst = body_rot_joint_listB[:]
        tail_joint_lst.reverse()

        splineIkJointList = rigData.JointLstCls.splineJointLst[:]
        splineIkJointList.reverse()

        main_ctrl_bend_attr = "{}.tailBend".format(rigData.OtherData.main_ctrl)
        main_ctrl_bendAgle_attr = "{}.tailBendAngle".format(rigData.OtherData.main_ctrl)
        main_ctrl_fallOff_attr = "{}.tailFallOff".format(rigData.OtherData.main_ctrl)
        core.bendExpContent(tail_joint_lst, splineIkJointList, "ry", tailBendLocalAttrLst,
                            main_ctrl_bend_attr, main_ctrl_bendAgle_attr, main_ctrl_fallOff_attr, self.system_name)

        core.hierarchy_conformity(body_rot_joint_listB,
                                  rigData.JointLstCls.bodyRotJointLstA,
                                  rigData.OtherData.body_fk_bn_ctrl_list)

        rigData.JointLstCls.bodyRotJointLstB = body_rot_joint_listB

    def bodyBendExpRig(self):
        u'''
        身体卷曲表达式绑定，并且处理了好层级关系
        '''
        body_rot_joint_listC = core.createBoneChainByOldBoneLst(self.body_joint_lst, self.system_name, "BodyRotJointC")
        bodyBendLocalAttrLst = []
        for fk_bn in rigData.OtherData.body_fk_bn_ctrl_list:
            if not core.hasAttr(fk_bn, "bodyBend"):
                cmds.addAttr(fk_bn, ln="bodyBend", at=u"double", dv=1, k=True)
            bodyBendLocalAttrLst.append("{}.bodyBend".format(fk_bn))


        main_ctrl_bend_attr = "{}.bodyBend".format(rigData.OtherData.main_ctrl)
        main_ctrl_bendAgle_attr = "{}.bodyBendAngle".format(rigData.OtherData.main_ctrl)
        main_ctrl_fallOff_attr = "{}.bodyFallOff".format(rigData.OtherData.main_ctrl)
        core.bendExpContent(body_rot_joint_listC, rigData.JointLstCls.splineJointLst, "ry", bodyBendLocalAttrLst,
                            main_ctrl_bend_attr, main_ctrl_bendAgle_attr, main_ctrl_fallOff_attr, self.system_name)

        core.hierarchy_conformity(body_rot_joint_listC,
                                  rigData.JointLstCls.bodyRotJointLstB,
                                  rigData.OtherData.body_fk_bn_ctrl_list)

        rigData.JointLstCls.bodyRotJointLstC = body_rot_joint_listC


    def bodyJointRig_conformity(self):
        u'''
        身体关节整合
        身体链接关节层级绑定
        身体约束关节制作
        身体约束关节属性链接
        '''
        body_rot_joint_listD = core.createBoneChainByOldBoneLst(self.body_joint_lst, self.system_name, "BodyRotJointD")
        core.hierarchy_conformity(body_rot_joint_listD,
                                  rigData.JointLstCls.bodyRotJointLstC,
                                  rigData.OtherData.body_fk_bn_ctrl_list)

        body_rot_joint_listE = core.createBoneChainByOldBoneLst(self.body_joint_lst, self.system_name, "BodyRotJointE")
        core.oneToOneConstraint(rigData.JointLstCls.splineJointLst, body_rot_joint_listE, 0, True)

        core.conAttr(body_rot_joint_listE, body_rot_joint_listD, "translate", "translate")
        core.conAttr(body_rot_joint_listE, body_rot_joint_listD, "rotate", "rotate")

        rigData.JointLstCls.bodyRotJointLstD = body_rot_joint_listD
        rigData.JointLstCls.bodyRotJointLstE = body_rot_joint_listE

    def control_conformity(self):
        u'''
        控制器整理
        控制器显示与隐藏链接
        控制定位器绑定
        定位器属性链接绑定
        '''
        core.conAttr([rigData.OtherData.main_ctrl], rigData.OtherData.fk_ctrl_shape_lst, "showFkCon", "visibility")

        main_ik_ctrl_lst = pyCore.getMainLst(rigData.OtherData.body_ik_con_lst)
        sub_ik_ctrl_lst = [i for i in rigData.OtherData.body_ik_con_lst if i not in main_ik_ctrl_lst]

        main_ik_grpA_lst = [rigData.OtherData.body_ik_conGrpA_lst[rigData.OtherData.body_ik_con_lst.index(i)] for i in main_ik_ctrl_lst]
        sub_ik_grpA_lst = [rigData.OtherData.body_ik_conGrpA_lst[rigData.OtherData.body_ik_con_lst.index(i)] for i in sub_ik_ctrl_lst]
        core.conAttr([rigData.OtherData.main_ctrl], main_ik_grpA_lst, "showIkCon", "visibility")
        core.conAttr([rigData.OtherData.main_ctrl], sub_ik_grpA_lst, "showIkSecondCon", "visibility")
        [cmds.color(sub_ik, rgb=[0.4, 0.8, 1]) for sub_ik in sub_ik_ctrl_lst]

        main_ik_loc_list = []
        main_ik_loc_group_list = []
        for main_ik in main_ik_ctrl_lst:
            index = rigData.OtherData.body_ik_con_lst.index(main_ik)
            loc = cmds.spaceLocator(n="{}PosLoc".format(main_ik))[0]
            loc_grp = cmds.group(em=True, n="{}GRP".format(loc))
            cmds.setAttr("{}.visibility".format(loc_grp), 0)
            core.propertyParent(loc, loc_grp)
            main_ik_loc_list.append(loc)
            main_ik_loc_group_list.append(loc_grp)
            core.propertyParent(loc_grp, rigData.OtherData.body_ik_conGrpA_lst[index])
            core.objZero(loc_grp)
            cmds.connectAttr("{}.translate".format(main_ik), "{}.translate".format(loc))
            cmds.connectAttr("{}.rotate".format(main_ik), "{}.rotate".format(loc))

        rigData.OtherData.main_ik_ctrl_lst = main_ik_ctrl_lst
        rigData.OtherData.sub_ik_ctrl_lst = sub_ik_ctrl_lst
        rigData.OtherData.main_ik_loc_list = main_ik_loc_list
        rigData.OtherData.sub_ik_grpA_lst = sub_ik_grpA_lst
        rigData.OtherData.main_ik_grpA_lst = main_ik_grpA_lst


    def subIk_transitionRig(self):
        u'''
        次级ik控制器过渡约束绑定
        过渡属性链接/缩放约束/父子约束
        '''
        new_con_grp_lst = core.giveGrpToObj(rigData.OtherData.body_ik_conGrp_lst)

        for main_ik_con, main_ik_loc in zip(rigData.OtherData.main_ik_ctrl_lst, rigData.OtherData.main_ik_loc_list):
            self_index = rigData.OtherData.main_ik_ctrl_lst.index(main_ik_con)
            global_first_index = rigData.OtherData.body_ik_con_lst.index(main_ik_con)
            cmds.scaleConstraint(main_ik_con, rigData.JointLstCls.bodyBindJointLst[global_first_index], mo=True,
                                 skip="x")
            joint_rotateX_attr = "{}.rotateX".format(rigData.JointLstCls.bodyBindJointLst[global_first_index])
            core.propertyConnectAttr("{}.rotateX".format(main_ik_con), joint_rotateX_attr)
            if self_index + 1 >= len(rigData.OtherData.main_ik_ctrl_lst):
                continue
            start_loc = rigData.OtherData.main_ik_loc_list[self_index]
            end_loc = rigData.OtherData.main_ik_loc_list[self_index+1]

            next_main_ik_ctrl = rigData.OtherData.main_ik_ctrl_lst[self_index+1]

            global_next_index = rigData.OtherData.body_ik_con_lst.index(next_main_ik_ctrl)

            con_grp_lst = new_con_grp_lst[global_first_index+1:global_next_index]
            core.averageCons(start_loc, end_loc, con_grp_lst, 0, True)

            sub_ik_joint_lst = rigData.JointLstCls.bodyBindJointLst[global_first_index+1:global_next_index]
            core.averageCons(main_ik_con, next_main_ik_ctrl, sub_ik_joint_lst, 3, True, "x")
            core.batchGradualConnect(main_ik_con, next_main_ik_ctrl, sub_ik_joint_lst)

        if len(self.body_joint_lst) % 2 == 0:
            ik_rx_attr = "{}.rotateX".format(rigData.OtherData.main_ik_ctrl_lst[-1])
            bind_joint_rx_attr = "{}.rotateX".format(rigData.JointLstCls.bodyBindJointLst[-1])
            core.propertyConnectAttr(ik_rx_attr, bind_joint_rx_attr)
            cmds.scaleConstraint(rigData.OtherData.main_ik_ctrl_lst[-1], rigData.JointLstCls.bodyBindJointLst[-1],
                                 mo=True, skip="x")

        rigData.OtherData.new_ik_con_grp_list = new_con_grp_lst

    def pathSplineRig(self):
        u'''
        路径样条绑定
        '''
        path_curve_grp = "{}GRP".format(self.path_curve)
        if not core.isEx(path_curve_grp):
            cmdCore.createOnlyOneGrp([path_curve_grp])
        core.propertyParent(path_curve_grp, rigData.GroupCls.noMoveGroup)
        core.propertyParent(self.path_curve, path_curve_grp)
        #cmds.parentConstraint(rigData.OtherData.main_ctrl, path_curve_grp, mo=True)
        #cmds.scaleConstraint(rigData.OtherData.main_ctrl, path_curve_grp, mo=True)
        
        path_joint_lst = core.createBoneChainByOldBoneLst(self.body_joint_lst, self.system_name, "PathJoint")
        core.reRootJnt(path_joint_lst[-1])
        path_joint_lst.reverse()
        path_ik_handle = cmdCore.createSplineIk(path_joint_lst[0], path_joint_lst[-1],
                                                self.path_curve, "{}_path_splineIk".format(self.system_name))
        core.splineIkAdvTwist(path_ik_handle, rigData.OtherData.main_ctrl, forwardType=1)

        # 此处的属性链接在之后需要断开，这里只是需要阶段性的看一下成果
        core.propertyConnectAttr("{}.pathOffset".format(rigData.OtherData.main_ctrl),
                                 "{}.offset".format(path_ik_handle))

        core.propertyParent(path_ik_handle, rigData.GroupCls.noMoveGroup)

        path_joint_lst.reverse()
        for ik_grp_A, path_joint in zip(rigData.OtherData.body_ik_conGrpA_lst, path_joint_lst):
            path_pos_loc = cmds.spaceLocator(n="{}PosLoc".format(path_joint))[0]
            cmds.setAttr("{}.visibility".format(path_pos_loc), 0)
            core.matchPos(path_joint, path_pos_loc)
            core.propertyParent(path_pos_loc, path_joint)
            cmds.parentConstraint(path_pos_loc, ik_grp_A, mo=True)

        path_joint_lst.reverse()

        rigData.OtherData.path_curve_grp = path_curve_grp
        rigData.JointLstCls.pathJointLst = path_joint_lst
        rigData.NodeCls.path_ik = path_ik_handle

    def createBJT_Joint(self):
        u'''
        创建蒙皮控制关节， BJT关节
        '''
        
        body_bjt_joint_lst = core.createBoneChainByOldBoneLst(self.body_joint_lst, self.system_name, "BJTA_Joint")
        core.oneToOneParent(rigData.OtherData.body_fk_bn_ctrl_list, body_bjt_joint_lst)

        rigData.JointLstCls.bodyBindJointBJTALst = body_bjt_joint_lst

    def createSinFat_joint(self):
        u'''
        创建正弦缩放关节 (fat关节)
        并且创建表达式
        '''
        
        body_fat_joint_list = core.createBoneChainByOldBoneLst(self.body_joint_lst, self.system_name, "FatJoint")
        coned_attrLst_sy = ["{}.sy".format(i) for i in body_fat_joint_list]
        coned_attrLst_sz = ["{}.sz".format(i) for i in body_fat_joint_list]
        fatSpeedAttr = "{}.fatSpeed".format(rigData.OtherData.main_ctrl)
        fatGoAttr = "{}.fatGo".format(rigData.OtherData.main_ctrl)
        fatDelayAttr = "{}.fatDelay".format(rigData.OtherData.main_ctrl)
        fatAttr = "{}.fat".format(rigData.OtherData.main_ctrl)
        exp_name = "{}_BodySinScaleExp".format(self.system_name)
        core.buildBodyFatScaleExp(coned_attrLst_sy, coned_attrLst_sz, fatSpeedAttr, fatGoAttr,
                                  fatDelayAttr, fatAttr, exp_name)

        core.oneToOneParent(rigData.OtherData.body_fk_bn_ctrl_list, body_fat_joint_list)

        rigData.JointLstCls.bodyFatJointLst = body_fat_joint_list

    def bodyWaveSplineIkRig(self):
        u'''
        身体波浪样条ik绑定
        '''
        body_wave_spline_joint_list = core.createBoneChainByOldBoneLst(self.body_joint_lst,
                                                          self.system_name, "BodyWaveSplineJoint")
        core.propertyParent(body_wave_spline_joint_list[0], rigData.NodeCls.bnLocNode)

        
        body_wave_joint_list = core.createBoneChainByOldBoneLst(self.body_joint_lst, self.system_name, "BodyWaveJoint")

        body_wave_ik_handle = cmdCore.createSplineIk(body_wave_spline_joint_list[0],
                                                     body_wave_spline_joint_list[-1],
                                                     rigData.NodeCls.bodyWaveCurve,
                                                     "{}_BodyWaveIkHandle".format(self.system_name))
        core.propertyParent(body_wave_ik_handle, rigData.GroupCls.noMoveGroup)
        core.oneToOneConstraint(body_wave_spline_joint_list, body_wave_joint_list, 1)

        body_wave_cluster_list = core.createCurveCluster(rigData.NodeCls.bodyWaveCurve, False, False)

        waveLocGrp = "{}_BodyWaveLocGrp".format(self.system_name)
        if not core.isEx(waveLocGrp):
            cmdCore.createOnlyOneGrp([waveLocGrp])

        body_wave_loc_list = []
        for wave_clu in body_wave_cluster_list:
            wave_loc = cmds.spaceLocator(n="{}PosLoc".format(wave_clu))[0]
            body_wave_loc_list.append(wave_loc)
            core.matchPos(wave_clu, wave_loc, 1)
            core.propertyParent(wave_clu, wave_loc)
            core.propertyParent(wave_loc, waveLocGrp)

        main_wave_loc = "{}_MainWaveLoc".format(self.system_name)
        if not core.isEx(main_wave_loc):
            cmds.spaceLocator(n=main_wave_loc)
        core.propertyParent(main_wave_loc, waveLocGrp)

        rigData.JointLstCls.splineWaveJointLst = body_wave_spline_joint_list
        rigData.JointLstCls.bodyWaveJointList = body_wave_joint_list
        rigData.NodeCls.wave_ik = body_wave_ik_handle
        rigData.NodeCls.main_wave_loc = main_wave_loc
        rigData.OtherData.body_wave_loc_list = body_wave_loc_list
        rigData.OtherData.body_wave_loc_grp = waveLocGrp

    def bodyWaveControlRig(self):
        u'''
        身体波浪控制器绑定
        '''
        main_wave_ctrl_name = "{}_BodyWaveCtrl".format(self.system_name)
        main_wave_control_list = cmdCore.createWaveCtrl(main_wave_ctrl_name)
        core.matchPos(main_wave_control_list[-1], rigData.NodeCls.main_wave_loc, 1)

        main_wave_ctrl_pathLoc = "{}_BodyWavePathLoc".format(self.system_name)
        if not core.isEx(main_wave_ctrl_pathLoc):
            cmds.spaceLocator(n=main_wave_ctrl_pathLoc)
        core.propertyParent(main_wave_ctrl_pathLoc, rigData.GroupCls.noMoveGroup)
        wave_motion_node = core.createMotionPath(self.path_curve, main_wave_ctrl_pathLoc,
                                                 "{}_BodyWaveMotionPath".format(self.system_name))
        core.propertyParent(main_wave_control_list[-1], main_wave_ctrl_pathLoc)
        core.objZero(main_wave_control_list[-1])
        cmds.scaleConstraint(rigData.OtherData.main_ctrl, main_wave_control_list[2], mo=True)
        cmds.pointConstraint(main_wave_control_list[0], rigData.NodeCls.main_wave_loc)
        cmds.select(self.path_curve, r=True)
        cmds.select(main_wave_control_list[-1], add=True)
        cmds.tangentConstraint(weight=1, aimVector=[0, 0, 1], upVector=[0, 1, 0], worldUpType="objectrotation",
                               worldUpVector=[0, 1, 0], worldUpObject=rigData.OtherData.main_ctrl)

        wave_fix_loc_list = []
        wave_point_constraint_list = []
        for fk_bn, wave_loc in zip(rigData.OtherData.body_fk_bn_ctrl_list, rigData.OtherData.body_wave_loc_list):
            wave_fix_loc = cmds.spaceLocator(n="{}Fix".format(wave_loc))[0]
            wave_fix_loc_list.append(wave_fix_loc)
            core.matchPos(wave_loc, wave_fix_loc, 1)
            cmds.pointConstraint(fk_bn, wave_fix_loc, mo=True)
            core.propertyParent(wave_fix_loc, rigData.OtherData.body_wave_loc_grp)
            wave_point_constraint = cmds.pointConstraint(rigData.NodeCls.main_wave_loc,
                                                         wave_fix_loc, wave_loc, skip="z", mo=True)[0]
            wave_point_constraint_list.append(wave_point_constraint)

        rigData.OtherData.body_main_wave_ctrl = main_wave_control_list[0]
        rigData.OtherData.body_main_wave_conGrp = main_wave_control_list[1]
        rigData.OtherData.body_main_wave_conGrpA = main_wave_control_list[2]
        rigData.NodeCls.driverMotionPath = wave_motion_node
        rigData.OtherData.wave_fix_loc_list = wave_fix_loc_list
        rigData.OtherData.wave_point_constraint_list = wave_point_constraint_list
        rigData.NodeCls.main_wave_ctrl_pathLoc = main_wave_ctrl_pathLoc

    def bodyWaveExpRig(self):
        u'''
        身体波浪表达式绑定
        '''
        cmdCore.mainWaveCtrlAddAttr(rigData.OtherData.body_main_wave_ctrl)
        body_wave_exp_name = "{}_BodyWaveExp".format(self.system_name)
        core.bodyWaveExp(rigData.OtherData.wave_fix_loc_list, rigData.OtherData.wave_point_constraint_list,
                         rigData.NodeCls.main_wave_loc, rigData.NodeCls.main_wave_ctrl_pathLoc,
                         "{}.waveWidth".format(rigData.OtherData.body_main_wave_ctrl), 1, body_wave_exp_name)

        wave_loc_grp_lst = core.giveGrpToObj(rigData.OtherData.body_wave_loc_list)
        [cmds.setAttr("{}.visibility".format(grp), 0) for grp in wave_loc_grp_lst]
        cmds.setAttr("{}.visibility".format(rigData.OtherData.body_wave_loc_grp), 0)
        core.propertyParent(rigData.OtherData.body_wave_loc_grp, rigData.GroupCls.noMoveGroup)
        core.oneToOneParent(rigData.OtherData.body_fk_bn_ctrl_list, wave_loc_grp_lst)

        # 身体波浪样条ik骨骼拉伸有问题
        cmdCore.waveSplineIkStretchRig(rigData.OtherData.main_ctrl, rigData.NodeCls.bodyWaveCurve,
                                       rigData.JointLstCls.splineWaveJointLst, scaleAxis="x")

    def bodySliderScaleExpRig(self):
        u'''
        身体滑动缩放表达式绑定/身体鼓包表达式绑定
        '''
        core.oneToOneParent(rigData.OtherData.body_fk_bn_ctrl_list, rigData.JointLstCls.bodyWaveJointList)
        core.bodySliderScaleExp(rigData.JointLstCls.bodyWaveJointList, rigData.OtherData.wave_fix_loc_list,
                                rigData.NodeCls.main_wave_ctrl_pathLoc, rigData.OtherData.body_main_wave_ctrl)
        core.disConnectAttr("{}.offset".format(rigData.NodeCls.path_ik))

        repairFollowPathLoc = "{}_RepairFollowPathLoc".format(self.system_name)
        if not core.isEx(repairFollowPathLoc):
            cmds.spaceLocator(n=repairFollowPathLoc)
        repair_calculateMotionPath = core.createMotionPath(self.path_curve, repairFollowPathLoc,
                                                           "{}_repairFollowMotionPath".format(self.system_name))

        cmdCore.waveCtrlFollowRig_connectAttr(rigData.OtherData.main_ctrl, rigData.OtherData.body_main_wave_ctrl,
                                              self.path_curve, rigData.NodeCls.driverMotionPath,
                                              repair_calculateMotionPath)
        cmds.setAttr("{}.rootOnCurve".format(rigData.NodeCls.path_ik), 0)
        cmds.pointConstraint(repairFollowPathLoc, rigData.JointLstCls.pathJointLst[0], mo=True)
        core.propertyParent(repairFollowPathLoc, rigData.GroupCls.noMoveGroup)

        rigData.NodeCls.repairFollowLoc = repairFollowPathLoc

    def bindJointLinkAttr(self):
        u'''
        身体绑定关节属性链接
        '''
        core.conAttr(rigData.JointLstCls.bodyBindJointLst, rigData.JointLstCls.bodyBindJointBJTALst,
                     "rotateX", "rotateX")
        core.threeJointaScaleCombineToOneJoint(rigData.JointLstCls.bodyWaveJointList,
                                               rigData.JointLstCls.bodyFatJointLst,
                                               rigData.JointLstCls.bodyBindJointLst,
                                               rigData.JointLstCls.bodyBindJointBJTALst)
        core.oneToOneConstraint(rigData.JointLstCls.bodyWaveJointList,
                                rigData.JointLstCls.bodyBindJointBJTALst, 1, True)
        core.animContraintBodyJoint(rigData.JointLstCls.bodyBindJointBJTALst, rigData.OtherData.body_fk_bn_ctrl_list)

    def headControlRig(self):
        u'''
        头部控制器绑定
        '''
        main_head_ctrl = "{}_MainHeadCtrl".format(self.system_name)
        main_head_ctrlGrp = "{}Grp".format(main_head_ctrl)
        main_head_ctrlGrpA = "{}GrpA".format(main_head_ctrl)
        if not core.isEx(main_head_ctrl):
            cmdCore.ballCtrl(main_head_ctrl, constValue.ValueCls.main_head_ctrl_size)
            cmds.group(em=True, n=main_head_ctrlGrp)
            cmds.parent(main_head_ctrl, main_head_ctrlGrp)
            cmds.group(em=True, n=main_head_ctrlGrpA)
            cmds.parent(main_head_ctrlGrp, main_head_ctrlGrpA)
            core.matchPos(self.body_joint_lst[0], main_head_ctrlGrpA)
        core.propertyParent(main_head_ctrlGrpA, rigData.OtherData.body_ik_conGrpA_lst[0])
        core.propertyParent(rigData.OtherData.neck_fk_conGrpA_lst[0], main_head_ctrl)
        core.propertyParent(rigData.OtherData.new_ik_con_grp_list[0], main_head_ctrl)
        cmds.parentConstraint(rigData.OtherData.main_ik_ctrl_lst[0], rigData.OtherData.neck_fk_conGrpA_lst[0], mo=True)

        rigData.OtherData.head_main_ctrl = main_head_ctrl

    def bodyScaleRepair(self):
        u'''
        修复身体关节整体缩放
        '''
        core.setJointScaleCompensateZero(rigData.JointLstCls.bodyBindJointLst, 0)

    def bodyAdvTwist(self):
        u'''
        身体高级扭曲
        '''
        if not core.hasAttr(rigData.OtherData.head_main_ctrl, "tailTwist"):
            cmds.addAttr(rigData.OtherData.head_main_ctrl, ln="tailTwist", at=u"double", dv=0, k=True)
        core.propertyConnectAttr("{}.tailTwist".format(rigData.OtherData.head_main_ctrl),
                                 "{}.twist".format(rigData.NodeCls.body_ik))
        cmds.setAttr("{}.dTwistControlEnable".format(rigData.NodeCls.body_ik), 1)
        cmds.setAttr("{}.dWorldUpType".format(rigData.NodeCls.body_ik), 4)

        tail_twist_ctrl = "{}_TailTwistCtrl".format(self.system_name)
        tail_twist_ctrlGrp = "{}Grp".format(tail_twist_ctrl)
        tail_twist_ctrlGrpA = "{}GrpA".format(tail_twist_ctrl)
        if not core.isEx(tail_twist_ctrl):
            cmdCore.ballCtrl(tail_twist_ctrl, constValue.ValueCls.main_head_ctrl_size)
            cmds.group(em=True, n=tail_twist_ctrlGrp)
            cmds.parent(tail_twist_ctrl, tail_twist_ctrlGrp)
            cmds.group(em=True, n=tail_twist_ctrlGrpA)
            cmds.parent(tail_twist_ctrlGrp, tail_twist_ctrlGrpA)
            core.matchPos(self.body_joint_lst[-1], tail_twist_ctrlGrpA)
        core.propertyParent(tail_twist_ctrlGrpA, rigData.OtherData.main_ik_grpA_lst[-1])

        core.propertyConnectAttr("{}.worldMatrix[0]".format(rigData.OtherData.head_main_ctrl),
                                 "{}.dWorldUpMatrix".format(rigData.NodeCls.body_ik))
        core.propertyConnectAttr("{}.worldMatrix[0]".format(tail_twist_ctrl),
                                 "{}.dWorldUpMatrixEnd".format(rigData.NodeCls.body_ik))

    def createSkinJointSet(self):
        u'''
        创建蒙皮骨骼选择集
        '''
        skin_joint_lst = rigData.JointLstCls.bodyBindJointBJTALst + self.neck_joint_lst[:-1]
        sets_name = "{}_SkinJointSets".format(self.system_name)
        if core.isEx(sets_name):
            cmds.delete(sets_name)
        cmds.sets(skin_joint_lst, n=sets_name)
        cmds.select(cl=True)

    def setVisZero(self):
        u'''
        将需要隐藏的物体隐藏
        '''
        outer_jnt_lst = [rigData.JointLstCls.bodyWaveJointList[0], rigData.JointLstCls.bodyRotJointLstE[0],
                   rigData.JointLstCls.splineJointLst[0], self.body_joint_lst[0],
                     rigData.JointLstCls.pathJointLst[0], rigData.JointLstCls.splineWaveJointLst[0]]
        
        ik_lst = [rigData.NodeCls.body_ik, rigData.NodeCls.path_ik,rigData.NodeCls.wave_ik,
                   rigData.NodeCls.bodySplineIkCurve, rigData.NodeCls.bodyWaveCurve]
        
        loc_lst = [rigData.NodeCls.bnLocNode, rigData.NodeCls.bnLocNodeA, rigData.NodeCls.main_wave_loc,
                    rigData.NodeCls.main_wave_ctrl_pathLoc, rigData.NodeCls.repairFollowLoc]
        loc_shape_lst = [core.getShpe(loc)[0] for loc in loc_lst]

        inter_jnt_lst = rigData.JointLstCls.bodyBindJointLst + rigData.JointLstCls.bodyFatJointLst + rigData.JointLstCls.bodyWaveJointList

        all_zero_lst = outer_jnt_lst + ik_lst + inter_jnt_lst + loc_shape_lst
        for i in all_zero_lst:
            if not i or not core.isEx(i):
                continue
            cmds.setAttr("{}.visibility".format(i), 0)

    def pathControllerSet(self):
        u'''
        路径曲线控制器创建
        '''
        path_driver_joint_grp = "{}_pathDriverJointGRP".format(self.system_name)
        cmdCore.createOnlyOneGrp([path_driver_joint_grp])
        path_driver_joint_list = core.createJointOnCurveCvPoint(self.path_curve, False)
        [core.propertyParent(i, path_driver_joint_grp) for i in path_driver_joint_list]
        cmds.skinCluster(path_driver_joint_list, self.path_curve, maximumInfluences=1)
        ik_ctrl_data = cmdCore.createIkCtrl(path_driver_joint_list, 3.5, [1,0,1], False)
        fk_ctrl_data = cmdCore.createFkCtrl(path_driver_joint_list, 2.5, [0.2,0.2,0.8], False)
        core.oneToOneParent(fk_ctrl_data["con"], ik_ctrl_data["conGrpALst"])
        core.oneToOneConstraint(ik_ctrl_data["conLst"], path_driver_joint_list, 3)
        core.propertyParent(fk_ctrl_data["conGrpA"][0], rigData.OtherData.main_ctrl)
        core.propertyParent(path_driver_joint_list[0], rigData.GroupCls.noMoveGroup)
        cmds.setAttr("{}.visibility".format(path_driver_joint_list[0]), 0)
        cmds.setAttr("{}.overrideEnabled".format(self.path_curve), 1)
        cmds.setAttr("{}.overrideDisplayType".format(self.path_curve), 2)
        core.propertyConnectAttr("{}.showPathCon".format(rigData.OtherData.main_ctrl), "{}.visibility".format(fk_ctrl_data["conGrpA"][0]))
        cmds.setAttr("{}.visibility".format(path_driver_joint_grp), 0)
        core.propertyParent(path_driver_joint_grp, rigData.GroupCls.noMoveGroup)
        cmds.select(cl=True)

    def endParent(self):
        u'''
        最后将骨骼p给定位器
        '''
        core.propertyParent(rigData.JointLstCls.bodyRotJointLstD[0], rigData.NodeCls.bnLocNode)
        core.propertyParent(rigData.JointLstCls.bodyRotJointLstE[0], rigData.NodeCls.bnLocNode)
        core.propertyParent(rigData.JointLstCls.pathJointLst[0], rigData.NodeCls.bnLocNode)
        cmds.select(cl=True)


    def doIt(self):
        self.step_01()
        self.createMainCtrl()
        self.createBodySplineIk()
        self.bodyStretchRig()
        self.bodySinExpRig()
        self.bodyFkCtrlRig()
        self.bodyBindJoint()
        self.bodyRotRig()
        self.tailBendExpRig()
        self.bodyBendExpRig()
        self.bodyJointRig_conformity()
        self.control_conformity()
        self.subIk_transitionRig()
        self.pathSplineRig()
        self.createBJT_Joint()
        self.createSinFat_joint()
        self.bodyWaveSplineIkRig()
        self.bodyWaveControlRig()
        self.bodyWaveExpRig()
        self.bodySliderScaleExpRig()
        self.bindJointLinkAttr()
        self.headControlRig()
        self.bodyScaleRepair()
        self.bodyAdvTwist()
        self.createSkinJointSet()
        self.setVisZero()
        self.pathControllerSet()
        self.endParent()