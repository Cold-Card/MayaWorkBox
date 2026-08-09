# -*- coding: utf 8 -*-

class JointLstCls:
    u'''
    记录关节链列表信息
    '''
    bodyJointLst = []  # 用于复制
    splineJointLst = []  # 线性ik骨骼
    bodyFkJointLst = []  # 身体fk骨骼，用于制作fk控制器
    pathJointLst = []  # 路径骨骼列表
    splineWaveJointLst = []  # 路径波浪骨骼列表
    bodyWaveJointList = []  # 身体波浪骨骼列表
    bodyFatJointLst = []  # 身体鼓包骨骼
    bodyBindJointLst = []  # bind 骨骼
    bodyBindJointBJTALst = []  # 教程中 最后的蒙皮骨骼

    # 以下是旋转骨骼
    bodyRotJointLstA = []
    bodyRotJointLstB = []
    bodyRotJointLstC = []
    bodyRotJointLstD = []
    bodyRotJointLstE = []

class NodeCls:
    u'''
    记录单个节点
    '''
    bnLocNode = None
    bnLocNodeA = None

    driverMotionPath = None
    calculateMotionPath = None

    body_ik = None
    path_ik = None
    wave_ik = None

    bodySplineIkCurve = None
    bodySplineIkCurveCopy = None
    bodyWaveCurve = None

    path_curve = None

    main_wave_loc = None
    main_wave_ctrl_pathLoc = None
    repairFollowLoc = None

class GroupCls:
    u'''
    记录所有组的名称
    从上往下，依次是
        mainGroup: 最上层组
        noMoveGroup: 不移动组
        locJointGroup: 骨骼组
    '''
    mainGroup = None

    noMoveGroup = None

    locJointGroup = None



class OtherData:
    u'''
    以上记录的是绑定中，分类明确并且很重要信息
    该类用于记录其他的杂项 （控制器 /控制器组/ 。。。）
    '''

    main_ctrl = None
    splineIkMainCtrlGroup = None
    path_curve_grp = None

    neck_fk_con_lst = []
    neck_fk_conGrp_lst = []
    neck_fk_conGrpA_lst = []

    body_ik_con_lst = []
    body_ik_conGrp_lst = []
    body_ik_conGrpA_lst = []

    body_fk_bn_ctrl_list = []
    fk_ctrl_shape_lst = []

    main_ik_ctrl_lst = []
    sub_ik_ctrl_lst = []

    main_ik_loc_list = []

    sub_ik_grpA_lst = []
    main_ik_grpA_lst = []
    new_ik_con_grp_list = []

    body_main_wave_ctrl = None
    body_main_wave_conGrp = None
    body_main_wave_conGrpA = None

    body_wave_loc_list = []
    wave_fix_loc_list = []
    wave_point_constraint_list = []

    body_wave_loc_grp = None

    head_main_ctrl = None
