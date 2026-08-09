# -*- coding: utf 8 -*-
import maya.mel as mel
import maya.cmds as cmds
from . import core

def ballCtrl(ball_ctrl_name, radius=0.5, rgb_c=[0, 1, 0]):
    u'''
    创建球形控制器
    '''
    nr_lst = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    cur_lst = []
    for n in nr_lst:
        cur = cmds.circle(r=radius, nr=n, ch=False)[0]
        cur_lst.append(cur)
    core.comBineShape(cur_lst[0], cur_lst[1:], True)
    cmds.rename(cur_lst[0], ball_ctrl_name)
    for shape in core.getShpe(ball_ctrl_name):
        cmds.color(shape, rgb=rgb_c)
    return ball_ctrl_name

def mainWaveCtrlAddAttr(ctrl):
    u'''
    身体波浪主控制器添加属性
    '''
    if not core.hasAttr(ctrl, "waveWidth"):
        cmds.addAttr(ctrl, ln="waveWidth", at=u"double", dv=8, min=1, k=True)
    if not core.hasAttr(ctrl, "follow"):
        cmds.addAttr(ctrl, ln="follow", at="bool", dv=1, k=True)
    if not core.hasAttr(ctrl, "offset"):
        cmds.addAttr(ctrl, ln="offset", at="double", min=0, max=1, dv=0.5, k=True)

def createWaveCtrl(ctrl_name, rgb_c=[0, 1, 0]):
    u'''
    创建身体波浪主控制器
    '''
    con_grp = cmds.group(em=True, n="{}ConGrp".format(ctrl_name))
    con_grpA = cmds.group(em=True, n="{}ConGrpA".format(ctrl_name))
    if core.isEx(ctrl_name):
        return [ctrl_name, con_grp, con_grpA]
    cmds.curve(n=ctrl_name, d=1, p=[[0, 0, -1], [-1, 0, 0], [0, 0, 1], [1, 0, 0], [0, 0, -1]])
    core.propertyParent(ctrl_name, con_grp)
    core.propertyParent(con_grp, con_grpA)
    cmds.color(ctrl_name, rgb=rgb_c)
    reverse_multy_node = core.node(core.NodeData.multyDivide)
    cmds.setAttr("{}.input2X".format(reverse_multy_node), -1)
    core.propertyConnectAttr("{}.translateZ".format(ctrl_name), "{}.input1X".format(reverse_multy_node))
    core.propertyConnectAttr("{}.outputX".format(reverse_multy_node), "{}.translateZ".format(con_grp))
    return [ctrl_name, con_grp, con_grpA]

def createSplineIk(root_jnt, end_jnt, curve_name, ik_name):
    u'''
    创建线性ik
    '''
    cmds.select(root_jnt, end_jnt, r=True)
    cmds.select(curve_name, add=True)
    ik_handle = cmds.ikHandle(n=ik_name, sol="ikSplineSolver", ccv=False, scv=False, pcv=False)[0]
    cmds.select(cl=True)
    return ik_handle

def createMainCtrl(ctrl_name, ctrl_radius=10, rgb_c = [1, 0, 0]):
    u'''
    创建主控制器
    '''
    if not core.isEx(ctrl_name):
        cmds.circle(n=ctrl_name, r=ctrl_radius, ch=False, nr=[0, 1, 0])
    ctrl_grp_name = "{}Grp".format(ctrl_name)
    if not core.isEx(ctrl_grp_name):
        createOnlyOneGrp([ctrl_grp_name])
    core.propertyParent(ctrl_name, ctrl_grp_name)
    cmds.color(ctrl_name, rgb=rgb_c)
    AddAttr(ctrl_name).doIt()
    return ctrl_grp_name

def createOnlyOneGrp(name_list):
    u'''
    创建唯一的组
    传入一个名称列表
    '''
    for grp_name in name_list:
        if core.isEx(grp_name):
            continue
        cmds.group(em=True, n=grp_name)
    cmds.select(cl=True)

def cubeCtrl(ctrlName, value=0.25):
    u'''
    立方体曲线
    '''
    ctrl = mel.eval('''curve -n {} -d 1
                        -p 0 0.5 0.5
                        -p 0 0.5 -0.5
                        -p 0 -0.5 -0.5
                        -p 0 -0.5 0.5
                        -p 0 0.5 0.5
                        -k 0 -k 1 -k 2 -k 3 -k 4 ;'''.format(ctrlName))
    cmds.setAttr("{}.scale".format(ctrl), value, value, value)
    cmds.makeIdentity(ctrl, apply=True)
    return ctrl

def createIkCtrl(lst, rValue=0.25, rgbLst=[1,0,0], parent=True):
    u'''
    创建ik控制器
    '''
    con_lst = []
    conGrp_lst = []
    conGrpA_lst = []
    for obj in lst:
        conName = "{}IkCon".format(obj)
        conGrpName = "{}Grp".format(conName)
        conGrpAName = "{}A".format(conGrpName)
        con = cubeCtrl(conName, rValue)
        cmds.color(con, rgb=rgbLst)
        con_lst.append(con)
        conGrp = cmds.group(con, n=conGrpName)
        conGrp_lst.append(conGrp)
        conGrpA = cmds.group(conGrp, n=conGrpAName)
        conGrpA_lst.append(conGrpA)
        cmds.delete(cmds.parentConstraint(obj, conGrpA))
        if parent == True:
            core.propertyParent(obj, con)
        else:
            cmds.parentConstraint(con, obj, mo=True)
    return {"conLst": con_lst, "conGrpLst": conGrp_lst, "conGrpALst": conGrpA_lst}

def createFkCtrl(obj_lst, ctrl_raius = 1, rgbc=[1,1,0], con=True):
    u'''
    fk控制器
    '''
    ctrl_lst = []
    ctrlGrp_lst = []
    ctrlGrpA_lst = []
    rotAttr_data = {"rotx": "Rotx", "roty": "Roty", "rotz": "Rotz"}
    rotAttr_lst = list(rotAttr_data.keys())
    rotate_attr_lst = ["rx", "ry", "rz"]

    for obj_index in range(len(obj_lst)):
        ctrl = cmds.circle(n="{}FkCon".format(obj_lst[obj_index]), ch=False, nr=[1, 0, 0], r=ctrl_raius)[0]
        ctrl_lst.append(ctrl)
        ctrlGrp = cmds.group(ctrl, n="{}Grp".format(ctrl))
        ctrlGrp_lst.append(ctrlGrp)
        ctrlGrpA = cmds.group(ctrlGrp, n="{}A".format(ctrlGrp))
        ctrlGrpA_lst.append(ctrlGrpA)
        cmds.delete(cmds.parentConstraint(obj_lst[obj_index], ctrlGrpA))
        if con == True:
            cmds.parentConstraint(ctrl, obj_lst[obj_index])
        if obj_index > 0:
            cmds.parent(ctrlGrpA, "{}FkCon".format(obj_lst[obj_index - 1]))

    for rotAttr, rotAttrNn in rotAttr_data.items():
        cmds.addAttr(ctrl_lst[-1], ln=rotAttr, nn=rotAttrNn, at="double", dv=0, k=True)
    cmds.addAttr(ctrl_lst[-1], ln="showCon", at="bool", k=True, dv=1)

    for ctrl in ctrl_lst[:-1]:
        ctrl_shape = cmds.listRelatives(ctrl, s=True)[0]
        cmds.connectAttr("{}.showCon".format(ctrl_lst[-1]), "{}.visibility".format(ctrl_shape))
    for conGrp in ctrlGrp_lst:
        for con_attr, rotate_attr in zip(rotAttr_lst, rotate_attr_lst):
            cmds.connectAttr("{}.{}".format(ctrl_lst[-1], con_attr), "{}.{}".format(conGrp, rotate_attr))

    cmds.color(ctrlGrpA_lst[0], rgb=rgbc)

    return {"con": ctrl_lst, "conGrp": ctrlGrp_lst, "conGrpA": ctrlGrpA_lst}

def stretchRig(main_ctrl, spline_curve, spline_joint_lst):
    u'''
    创建线性ik简易拉伸绑定
    第一个参数是 主控制器
    第二个参数是 线性ik的曲线
    第三个参数是 线性ik骨骼的名称列表
    '''
    input2x_name = "{}{}X".format(core.NodeData.input_attr, 2)
    input1x_name = "{}{}X".format(core.NodeData.input_attr, 1)

    AddAttr(main_ctrl).addStretchAttr()
    curve_shape = core.getShpe(spline_curve)[0]
    curveInfo_node = core.node(core.NodeData.curveInfo)
    input_curve_attr = "{}.{}".format(curveInfo_node, core.NodeData.inputCurve)
    shape_world_space_attr = "{}.{}".format(curve_shape, core.NodeData.worldSpace)
    core.propertyConnectAttr(shape_world_space_attr, input_curve_attr)
    arc_length_value = cmds.getAttr("{}.{}".format(curveInfo_node, core.NodeData.arcLength))

    multy_01_node = core.node(core.NodeData.multyDivide)
    input2x_01 = "{}.{}".format(multy_01_node, input2x_name)
    cmds.setAttr(input2x_01, arc_length_value)
    input1x_01 = "{}.{}".format(multy_01_node, input1x_name)
    core.propertyConnectAttr("{}.{}Z".format(main_ctrl, core.NodeData.scale), input1x_01)

    multy_02_node = core.node(core.NodeData.multyDivide)
    cmds.setAttr("{}.{}".format(multy_02_node, core.NodeData.operation), 2)
    core.propertyConnectAttr("{}.{}".format(curveInfo_node, core.NodeData.arcLength),
                             "{}.{}".format(multy_02_node, input1x_name))
    core.propertyConnectAttr("{}.{}X".format(multy_01_node, core.NodeData.output_attr),
                             "{}.{}".format(multy_02_node, input2x_name))

    condition_01_node = core.node(core.NodeData.condition)
    cmds.setAttr("{}.{}".format(condition_01_node, core.NodeData.operation), 2)
    core.propertyConnectAttr("{}.{}X".format(multy_02_node, core.NodeData.output_attr),
                             "{}.{}".format(condition_01_node, core.NodeData.firstTerm))
    core.propertyConnectAttr("{}.{}X".format(multy_02_node, core.NodeData.output_attr),
                             "{}.{}R".format(condition_01_node, core.NodeData.colorIfTrue))
    core.propertyConnectAttr("{}.stretch_limit".format(main_ctrl),
                             "{}.{}".format(condition_01_node, core.NodeData.secondTerm))
    core.propertyConnectAttr("{}.stretch_limit".format(main_ctrl),
                             "{}.{}R".format(condition_01_node, core.NodeData.colorIfFalse))

    condition_02_node = core.node(core.NodeData.condition)
    cmds.setAttr("{}.{}".format(condition_02_node, core.NodeData.operation), 4)
    core.propertyConnectAttr("{}.{}R".format(condition_01_node, core.NodeData.outColor),
                             "{}.{}R".format(condition_02_node, core.NodeData.colorIfTrue))
    core.propertyConnectAttr("{}.{}R".format(condition_01_node, core.NodeData.outColor),
                             "{}.{}".format(condition_02_node, core.NodeData.firstTerm))
    core.propertyConnectAttr("{}.stretch".format(main_ctrl),
                             "{}.{}R".format(condition_02_node, core.NodeData.colorIfFalse))
    core.propertyConnectAttr("{}.stretch".format(main_ctrl),
                             "{}.{}".format(condition_02_node, core.NodeData.secondTerm))

    condition_02_outColor_attr = "{}.{}R".format(condition_02_node, core.NodeData.outColor)

    for spline_joint in spline_joint_lst:
        core.propertyConnectAttr(condition_02_outColor_attr, "{}.{}X".format(spline_joint, core.NodeData.scale))

    cmds.select(cl=True)

def jointToFkCtrl(fk_jnt_lst, ctrl_radius=0.5, rgb_c = [1, 1, 0]):
    u'''
    将骨骼链变成fk控制器
    （给骨骼添加曲线的形状节点，使之变成曲线）
    '''
    if not fk_jnt_lst:
        return
    shape_lst = []
    for fk_jnt in range(len(fk_jnt_lst)):
        cur = cmds.circle(n="bodyFkCurveA{}".format(fk_jnt+1), nr=(1, 0, 0), ch=False, r=ctrl_radius)[0]
        cur_shape = cmds.listRelatives(cur, s=True)[0]
        shape_lst.append(cur_shape)
        cmds.parent(cur_shape, fk_jnt_lst[fk_jnt], r=True, s=True)
        cmds.delete(cur)
        cmds.color(cur_shape, rgb=rgb_c)
    cmds.select(cl=True)
    return shape_lst

def waveSplineIkStretchRig(main_ctrl, waveSplineIkCurve, waveSplineIkJointLst, scaleAxis="x"):
    u'''
    身体波浪线性ik骨骼拉伸绑定
    main_ctrl:主控制器
    waveSplineIkCurve: 波浪线性ik曲线
    waveSplineIkJointLst: 波浪线性ik骨骼列表
    '''
    waveSplineIkCurveShape = core.getShpe(waveSplineIkCurve)[0]

    curve_info_node = core.node(core.NodeData.curveInfo)
    multy_01_node = core.node(core.NodeData.multyDivide)
    multy_02_node = core.node(core.NodeData.multyDivide)
    cmds.setAttr("{}.{}".format(multy_02_node, core.NodeData.operation), 2)

    cmds.connectAttr("{}.{}".format(waveSplineIkCurveShape, core.NodeData.worldSpace),
                     "{}.{}".format(curve_info_node, core.NodeData.inputCurve))

    arc_length = cmds.getAttr("{}.{}".format(curve_info_node, core.NodeData.arcLength))

    cmds.connectAttr("{}.{}Z".format(main_ctrl, core.NodeData.scale),
                     "{}.{}1X".format(multy_01_node, core.NodeData.input_attr))
    cmds.setAttr("{}.{}2X".format(multy_01_node, core.NodeData.input_attr), arc_length)

    cmds.connectAttr("{}.{}".format(curve_info_node, core.NodeData.arcLength),
                     "{}.{}1X".format(multy_02_node, core.NodeData.input_attr))
    cmds.connectAttr("{}.{}X".format(multy_01_node, core.NodeData.output_attr),
                     "{}.{}2X".format(multy_02_node, core.NodeData.input_attr))

    for jnt in waveSplineIkJointLst:
        cmds.connectAttr("{}.{}X".format(multy_02_node, core.NodeData.output_attr),
                         "{}.s{}".format(jnt, scaleAxis))

def waveCtrlFollowRig_connectAttr(main_ctrl, wave_ctrl, path_curve, motionPath_1, motionPath_2, setRangeOldMaxValue=100):
    u'''
    波浪控制器跟随绑定，就是第十一章那个很烦的属性链接部分
    main_ctrl: 主控制器
    wave_ctrl：波浪控制器
    path_curve：路径曲线
    motionPath_1：路径动画节点 （将波浪控制器锁定在路径曲线上的那个路径动画节点）
    motionPath_2:第二个路径动画节点 （用于修正计算跟随百分比的那个路径动画节点）
    setRangeOldMaxValue：主控制器的路径偏移属性（offset属性）的最大值
    '''
    path_curveShape = cmds.listRelatives(path_curve, s=True)[0]

    setRangeNode = cmds.createNode("setRange")
    cmds.setAttr("{}.oldMaxX".format(setRangeNode), setRangeOldMaxValue)
    cmds.setAttr("{}.maxX".format(setRangeNode), 1)
    cmds.connectAttr("{}.pathOffset".format(main_ctrl), "{}.valueX".format(setRangeNode))
    cmds.connectAttr("{}.outValueX".format(setRangeNode), "{}.uValue".format(motionPath_2))

    curveInfoNode = cmds.createNode("curveInfo")
    cmds.connectAttr("{}.worldSpace[0]".format(path_curveShape), "{}.inputCurve".format(curveInfoNode))

    multy_01_node = cmds.createNode("multiplyDivide")
    cmds.connectAttr("{}.scaleZ".format(main_ctrl), "{}.input2X".format(multy_01_node))
    cmds.connectAttr("{}.translateZ".format(wave_ctrl), "{}.input1X".format(multy_01_node))

    multy_02_node = cmds.createNode("multiplyDivide")
    cmds.setAttr("{}.operation".format(multy_02_node), 2)
    cmds.connectAttr("{}.outputX".format(multy_01_node), "{}.input1X".format(multy_02_node))
    cmds.connectAttr("{}.arcLength".format(curveInfoNode), "{}.input2X".format(multy_02_node))

    plus_01_node = cmds.createNode("plusMinusAverage")
    cmds.connectAttr("{}.offset".format(wave_ctrl), "{}.input3D[0].input3Dx".format(plus_01_node))
    cmds.connectAttr("{}.outputX".format(multy_02_node), "{}.input3D[1].input3Dx".format(plus_01_node))

    plus_02_node = cmds.createNode("plusMinusAverage")
    cmds.connectAttr("{}.output3Dx".format(plus_01_node), "{}.input3D[0].input3Dx".format(plus_02_node))
    cmds.connectAttr("{}.outValueX".format(setRangeNode), "{}.input3D[1].input3Dx".format(plus_02_node))

    condition_node = cmds.createNode("condition")
    cmds.setAttr("{}.secondTerm".format(condition_node), 1)
    cmds.connectAttr("{}.follow".format(wave_ctrl), "{}.firstTerm".format(condition_node))
    cmds.connectAttr("{}.output3Dx".format(plus_01_node), "{}.colorIfFalseR".format(condition_node))
    cmds.connectAttr("{}.output3Dx".format(plus_02_node), "{}.colorIfTrueR".format(condition_node))
    cmds.connectAttr("{}.outColorR".format(condition_node), "{}.uValue".format(motionPath_1))

class AddAttr:
    u'''
    给物体添加属性的类
    '''
    def __init__(self, obj):
        self.obj = obj

    def addStretchAttr(self):
        u'''
        添加拉伸绑定属性
        '''
        stretch_attr_lst = [u"stretch_attr", u"stretch", u"stretch_limit"]
        for attr in stretch_attr_lst:
            if attr == u"stretch" and not core.hasAttr(self.obj, attr):
                cmds.addAttr(self.obj, ln=attr, at=u"double", min=1, max=10, dv=2.0, k=True)
            elif attr == u"stretch_limit" and not core.hasAttr(self.obj, attr):
                cmds.addAttr(self.obj, ln=attr, at=u"double", min=0.1, max=1, dv=0.5, k=True)
            elif attr == u"stretch_attr" and not core.hasAttr(self.obj, attr):
                cmds.addAttr(self.obj, ln=attr, at="bool", k=True)
                core.lockAttr("{}.{}".format(self.obj, attr))

    def addSinAttr(self):
        u'''
        添加正弦控制属性
        '''
        sin_attr_lst = ["sinAttr", "speed", "width", "go", "delay", "addWidth"]
        for attr in sin_attr_lst:
            if attr == "sinAttr" and not core.hasAttr(self.obj, attr):
                cmds.addAttr(self.obj, ln=attr, at="bool", k=True)
                core.lockAttr("{}.{}".format(self.obj, attr))
            elif attr == "speed" and not core.hasAttr(self.obj, attr):
                cmds.addAttr(self.obj, ln=attr, at=u"double", min=0, dv=0, k=True)
            elif attr == "width" and not core.hasAttr(self.obj, attr):
                cmds.addAttr(self.obj, ln=attr, at=u"double", min=0, max=10, dv=0, k=True)
            elif attr == "go" and not core.hasAttr(self.obj, attr):
                cmds.addAttr(self.obj, ln=attr, at=u"double", dv=0, k=True)
            elif attr == "delay" and not core.hasAttr(self.obj, attr):
                cmds.addAttr(self.obj, ln=attr, at=u"double", min=0, dv=0.5, k=True)
            elif attr == "addWidth" and not core.hasAttr(self.obj, attr):
                cmds.addAttr(self.obj, ln=attr, at=u"double", dv=-0.025, k=True)

    def addRotAttr(self):
        u'''
        添加整体旋转控制属性
        '''
        attr_lst = ["rotAttr", "rotx", "roty", "rotz"]
        for attr in range(len(attr_lst)):
            if attr == 0:
                if not core.hasAttr(self.obj, attr_lst[attr]):
                    cmds.addAttr(self.obj, ln=attr_lst[attr], at="bool", k=True)
                    core.lockAttr("{}.{}".format(self.obj, attr_lst[attr]))
            else:
                if not core.hasAttr(self.obj, attr_lst[attr]):
                    cmds.addAttr(self.obj, ln=attr_lst[attr], dv=0, k=True)

    def addTailBendAttr(self):
        u'''
        添加尾部卷曲绑定属性
        '''
        tailBendAttrLst = [u"tailBendAttr", "tailBend", "tailBendAngle", "tailFallOff"]

        for tail_attr in tailBendAttrLst:
            if tail_attr == u"tailBendAttr":
                if not core.hasAttr(self.obj, tail_attr):
                    cmds.addAttr(self.obj, ln=tail_attr, at="bool", k=True)
                    core.lockAttr("{}.{}".format(self.obj, tail_attr))
            else:
                if not core.hasAttr(self.obj, tail_attr):
                    cmds.addAttr(self.obj, ln=tail_attr, at=u"double", dv=0, k=True)
        cmds.setAttr("{}.tailBendAngle".format(self.obj), 45)
        cmds.setAttr("{}.tailFallOff".format(self.obj), 1)

    def addBodyBendAttr(self):
        u'''
        添加身体卷曲绑定属性
        '''
        bodyBendAttrLst = [u"bodyBendAttr", "bodyBend", "bodyBendAngle", "bodyFallOff"]
        for body_attr in bodyBendAttrLst:
            if body_attr == u"bodyBendAttr":
                if not core.hasAttr(self.obj, body_attr):
                    cmds.addAttr(self.obj, ln=body_attr, at="bool", k=True)
                    core.lockAttr("{}.{}".format(self.obj, body_attr))
            else:
                if not core.hasAttr(self.obj, body_attr):
                    cmds.addAttr(self.obj, ln=body_attr, at=u"double", dv=0, k=True)
        cmds.setAttr("{}.bodyBendAngle".format(self.obj), 45)
        cmds.setAttr("{}.bodyFallOff".format(self.obj), 1)

    def addShowAttr(self):
        u'''
        添加控制器显示隐藏属性
        '''
        showAttrLst = ["showAttr", "showFkCon", "showIkCon", "showIkSecondCon", "showPathCon"]
        for attr in showAttrLst:
            if attr == "showAttr":
                if not core.hasAttr(self.obj, attr):
                    cmds.addAttr(self.obj, ln=attr, at="bool", k=True)
                    core.lockAttr("{}.{}".format(self.obj, attr))
            else:
                if not core.hasAttr(self.obj, attr):
                    cmds.addAttr(self.obj, ln=attr, at="bool",dv=1, k=True)
        cmds.setAttr("{}.showPathCon".format(self.obj), 0)


    def addPathAttr(self):
        u'''
        添加路径动画属性
        '''
        attr_lst = ["pathAttr", "pathOffset"]
        for attr in attr_lst:
            if attr == "pathAttr" and not core.hasAttr(self.obj, attr):
                cmds.addAttr(self.obj, ln=attr, at="bool", k=True)
                core.lockAttr("{}.{}".format(self.obj, attr))
            elif attr == "pathOffset" and not core.hasAttr(self.obj, attr):
                cmds.addAttr(self.obj, ln=attr, at=u"double", dv=0, min=0, max=100,k=True)

    def addFatAttr(self):
        u'''
        添加正弦缩放控制属性
        '''
        attr_lst = ["fatAttr", "fatSpeed", "fat", "fatGo", "fatDelay"]
        for attr in attr_lst:
            if attr == "fatAttr":
                if not core.hasAttr(self.obj, attr):
                    cmds.addAttr(self.obj, ln=attr, at="bool", k=True)
                    core.lockAttr("{}.{}".format(self.obj, attr))
            else:
                if not core.hasAttr(self.obj, attr):
                    cmds.addAttr(self.obj, ln=attr, at=u"double", dv=0, k=True)


    def doIt(self):
        u'''
        为主控制器添加所有所需的控制属性
        '''
        self.addStretchAttr()
        self.addSinAttr()
        self.addRotAttr()
        self.addTailBendAttr()
        self.addBodyBendAttr()
        self.addShowAttr()
        self.addPathAttr()
        self.addFatAttr()
