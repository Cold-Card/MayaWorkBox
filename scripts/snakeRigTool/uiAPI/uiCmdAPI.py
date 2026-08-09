# -*- coding: utf 8 -*-
import maya.cmds as cmds
from . import uiTempData
from ..script import core
from ..utility import rigSystem, constValue

def pos_joint(start_obj, end_obj, jnt_name, value=0.9):
    u'''
    在插件主要用于创建蛇类颈部骨骼
    函数名不知道叫什么好，就先叫这个吧
    '''
    cmds.select(cl=True)
    if not cmds.objExists(jnt_name):
        jnt = cmds.joint(n=jnt_name)
    point_con = cmds.pointConstraint(start_obj, end_obj, jnt_name)[0]
    cmds.setAttr("{}.{}W0".format(point_con, start_obj), value)
    cmds.setAttr("{}.{}W1".format(point_con, end_obj), 1-value)
    cmds.delete(point_con)
    return jnt_name

def createJoint(jntName, pos):
    u'''
    创建关节
    '''
    cmds.select(cl=True)
    if not cmds.objExists(jntName):
        cmds.joint(n=jntName)
    cmds.setAttr("{}.translate".format(jntName), *pos)
    return jntName

def getMeshZ_AxisValue(obj):
    u'''
    获取模型boudingbox的z轴的数值
    '''
    value_lst = cmds.exactWorldBoundingBox(obj)
    end_z_value = value_lst[2]
    start_z_value = value_lst[-1]
    return [start_z_value, end_z_value]

def get_mid_pos(start_pos, end_pos, mid_number):
    u'''
    获取两个坐标之间的几等份坐标
    例如：
        start_pos = [0,0,0]
        end_pos = [2,2,2]
        mid_number = 4
        这代表在开始和结束这两点坐标之间，获取四等分的坐标
        返回结果是： [[0.4, 0.4, 0.4],
                   [0.8, 0.8, 0.8],
                   [1.2000000000000002, 1.2000000000000002, 1.2000000000000002],
                   [1.6, 1.6, 1.6]]
    '''
    sub_pos = [t-i for i, t in zip(start_pos, end_pos)]
    step_pos = [float(i)/(mid_number+1) for i in sub_pos]
    main_list = []
    for i in range(1, mid_number+1):
        add_lis = [n*i for n in step_pos]
        real_lis = [s+t for s, t in zip(start_pos, add_lis)]
        main_list.append(real_lis)
    return main_list

def insert_joint(root_jnt, pos):
    u'''
    插入骨骼，输入根骨骼，再输入插入骨骼的坐标
    即可在目标位置生成插入骨骼
    '''
    insert_jnt = cmds.insertJoint(root_jnt)
    cmds.joint(insert_jnt, e=True, co=True, p=pos)
    return insert_jnt

root_joint = "joint1"
end_joint = "joint2"
mid_number = 10

def insertJointCmd(root_joint, end_joint, mid_number):
    u'''
    插入关节命令
    用于快速创建身体/脖子的关节
    '''
    start_pos = cmds.xform(root_joint, ws=True, t=True, q=True)
    end_pos = cmds.xform(end_joint, ws=True, t=True, q=True)

    pos_list = get_mid_pos(start_pos, end_pos, mid_number)
    pos_list.reverse()

    insert_joint_lst = []
    for i in pos_list:
        inser_jnt = insert_joint(root_joint, i)
        insert_joint_lst.append(inser_jnt)
    return insert_joint_lst

def removeJoint(insert_joint_lst):
    u'''
    移除插入的关节
    '''
    cmds.select(insert_joint_lst, r=True)
    cmds.RemoveJoint()

def createNeckBodySE_joint(system_name, mesh):
    u'''
    创建脖子/身体定位导航骨骼
    '''
    z_axis_list = getMeshZ_AxisValue(mesh)
    body_end_pos = z_axis_list[-1]
    head_end_pos = z_axis_list[0]
    length = head_end_pos - body_end_pos

    body_end_joint = createJoint("{}_{}_BodyEndJoint".format(system_name, mesh), [0, 0, body_end_pos])
    head_end_joint = createJoint("{}_{}_HeadEndJoint".format(system_name, mesh), [0, 0, head_end_pos])

    body_start_joint = pos_joint(head_end_joint, body_end_joint, "{}_{}_BodyGuideJoint".format(system_name, mesh))
    neck_start_joint = pos_joint(head_end_joint, body_end_joint, "{}_{}_NeckGuideJoint".format(system_name, mesh))

    head_joint = pos_joint(head_end_joint, neck_start_joint, "{}_{}_HeadGuideJoint".format(system_name, mesh), 0.5)

    path_guide_joint = createJoint("{}_{}_PathGuideJoint".format(system_name, mesh), [0, 0, head_end_pos + length])


    uiTempData.TempJoint.body_end_joint = body_end_joint
    uiTempData.TempJoint.head_end_joint = head_end_joint
    uiTempData.TempJoint.neck_start_joint = neck_start_joint
    uiTempData.TempJoint.body_start_joint = body_start_joint
    uiTempData.TempJoint.head_joint = head_joint
    uiTempData.TempJoint.path_guide_joint = path_guide_joint


def realTimeCreateJoint(inser_num, body=True):
    u'''
    实时创建骨骼
    system_name:绑定系统的名称
    body:判断是创建身体骨骼还是脖子骨骼
    '''
    cmds.select(cl=True)
    if body == True:
        if uiTempData.TempJoint.body_insert_joint_list:
            ex_lst = [i for i in uiTempData.TempJoint.body_insert_joint_list if cmds.objExists(i)]
            if ex_lst:
                removeJoint(ex_lst)
        if not uiTempData.TempJoint.body_start_joint or not uiTempData.TempJoint.body_end_joint:
            return

        if not core.isEx(uiTempData.TempJoint.body_start_joint) or not core.isEx(uiTempData.TempJoint.body_end_joint):
            return
        body_insert_joint_list = insertJointCmd(uiTempData.TempJoint.body_start_joint,
                                                uiTempData.TempJoint.body_end_joint, inser_num)
        uiTempData.TempJoint.body_insert_joint_list = body_insert_joint_list
    else:
        if uiTempData.TempJoint.neck_insert_joint_list:
            ex_lst = [i for i in uiTempData.TempJoint.neck_insert_joint_list if cmds.objExists(i)]
            if ex_lst:
                removeJoint(ex_lst)
        if not uiTempData.TempJoint.neck_start_joint or not uiTempData.TempJoint.head_joint:
            return

        if not core.isEx(uiTempData.TempJoint.neck_start_joint) or not core.isEx(uiTempData.TempJoint.head_joint):
            return
        neck_insert_joint_list = insertJointCmd(uiTempData.TempJoint.neck_start_joint,
                                                uiTempData.TempJoint.head_joint, inser_num)
        uiTempData.TempJoint.neck_insert_joint_list = neck_insert_joint_list

def guideComplete(system_name, mid_number):
    u'''
    创建导航骨骼父子关系
    '''
    if not uiTempData.TempJoint.body_end_joint or not core.isEx(uiTempData.TempJoint.body_end_joint)\
        or not uiTempData.TempJoint.body_start_joint or not core.isEx(uiTempData.TempJoint.body_start_joint)\
        or not uiTempData.TempJoint.head_end_joint or not core.isEx(uiTempData.TempJoint.head_end_joint)\
        or not uiTempData.TempJoint.head_joint or not core.isEx(uiTempData.TempJoint.head_joint)\
        or not uiTempData.TempJoint.neck_start_joint or not core.isEx(uiTempData.TempJoint.neck_start_joint):
        return
    core.propertyParent(uiTempData.TempJoint.body_end_joint, uiTempData.TempJoint.body_start_joint)
    core.propertyParent(uiTempData.TempJoint.head_end_joint, uiTempData.TempJoint.head_joint)
    core.propertyParent(uiTempData.TempJoint.head_joint, uiTempData.TempJoint.neck_start_joint)
    start_pos = cmds.xform(uiTempData.TempJoint.body_end_joint, ws=True, t=True, q=True)
    end_pos = cmds.xform(uiTempData.TempJoint.path_guide_joint, ws=True, t=True, q=True)
    path_curve_pos = get_mid_pos(start_pos, end_pos, mid_number)
    path_curve_pos.insert(0, start_pos)
    path_curve_pos.append(end_pos)
    path_curve = cmds.curve(n="{}_PathCurve".format(system_name), d=3, p=path_curve_pos)
    uiTempData.TempJoint.path_curve = path_curve

def xyyJointAxis(root, end):
    u'''
    使骨骼链的轴向为xyy模式
    '''
    cmds.joint(root, e=True, oj="xyz", secondaryAxisOrient="yup", ch=True, zso=True)
    cmds.joint(end, e=True, oj="none", ch=True)

def buildRigCmd(system_name):
    u'''
    创建绑定系统命令
    '''
    if not uiTempData.TempJoint.body_start_joint\
            or not uiTempData.TempJoint.neck_start_joint\
            or not uiTempData.TempJoint.path_guide_joint:
        return
    body_joint_lst = core.duplicateJoint(uiTempData.TempJoint.body_start_joint, system_name, "BodyJoint")
    neck_joint_lst = core.duplicateJoint(uiTempData.TempJoint.neck_start_joint, system_name, "NeckJoint")
    head_end_name = "{}_HeadEndJoint".format(system_name)
    cmds.rename(neck_joint_lst[-1], head_end_name)
    head_name = "{}_HeadJoint".format(system_name)
    cmds.rename(neck_joint_lst[-2], head_name)
    neck_joint_lst[-1] = head_end_name
    neck_joint_lst[-2] = head_name

    xyyJointAxis(neck_joint_lst[0], neck_joint_lst[-1])
    xyyJointAxis(body_joint_lst[0], body_joint_lst[-1])

    rigSystem.SnakeRigSystem(system_name, body_joint_lst, neck_joint_lst, uiTempData.TempJoint.path_curve).doIt()

    cmds.delete(uiTempData.TempJoint.body_start_joint)
    cmds.delete(uiTempData.TempJoint.neck_start_joint)
    cmds.delete(uiTempData.TempJoint.path_guide_joint)