# -*- coding: utf 8 -*-
import os
from . import pyCore
import maya.cmds as cmds
import maya.mel as mel
import maya.OpenMaya as OpenMaya

def createJointOnCurveCvPoint(curve, par=True):
    u'''
    在曲线所有的cv点上，创建关节
    '''
    cv_lst = cmds.ls("{}.cv[:]".format(curve), fl=True)
    joint_lst = []
    n = 1
    for cv in cv_lst:
        cmds.select(cl=True)
        jnt = cmds.joint(n="{}_{}_joint".format(curve, n))
        cv_pos = cmds.xform(cv, ws=True, t=True, q=True)
        cmds.setAttr("{}.translate".format(jnt), *cv_pos)
        cmds.setAttr("{}.jointOrientY".format(jnt), -90)
        joint_lst.append(jnt)
        if par == True:
            if n > 1:
                cmds.parent(jnt, "{}_{}_joint".format(curve, n-1))
        n += 1
    return joint_lst

def setCurveLineWidth(curve_lst, size=2):
    u'''
    设置曲线lineWidth属性
    '''
    for cur in curve_lst:
        if not isEx(cur):
            continue
        cmds.setAttr("{}.lineWidth".format(cur), size)

def createBoneChainByOldBoneLst(old_bone_lst, system_name, subfix_name):
    u'''
    通过一个骨骼列表生成一个新的骨骼链
    原始骨骼名称列表
    绑定系统名称
    骨骼名称后缀
    '''
    new_bone_lst = []
    for old in old_bone_lst:
        current_index = old_bone_lst.index(old)
        cmds.select(cl=True)
        new_jnt = cmds.joint(n="{}_{}_{}".format(system_name, current_index+1, subfix_name))
        new_bone_lst.append(new_jnt)
        matchPos(old, new_jnt)
        cmds.makeIdentity(new_jnt, apply=True)
        if current_index > 0:
            propertyParent(new_jnt, "{}_{}_{}".format(system_name, current_index, subfix_name))
    return new_bone_lst


def importFile(path):
    u'''
    导入ma文件命令
    '''
    if not os.path.exists(path):
        return
    mel.eval('''file -import -type "mayaAscii"  -ignoreVersion
                -ra true -mergeNamespacesOnClash true -namespace ":"
                -options "v=0;"  -pr  -importTimeRange "combine" "{}";'''.format(path))

def addShape(cur_1, cur_2, delete=True):
    u'''
    添加曲线形状
    将cur_1的形状节点都加到cur_2中
    delete为True时，删除cur_1
    '''
    cur_1_shape = cmds.listRelatives(cur_1, s=True)
    if isinstance(cur_1_shape, list):
        for shape in cur_1_shape:
            cmds.parent(shape, cur_2, r=True, s=True)
    else:
        cmds.parent(cur_1_shape, cur_2, r=True, s=True)
    if delete == True:
        cmds.delete(cur_1)
    cmds.select(cl=True)

def comBineShape(cur, other, delete = True):
    u'''
    合并形状节点
    '''
    if not cmds.objExists(cur):
        return
    for o in other:
        if not cmds.objExists(o):
            continue
        addShape(o, cur, delete)
    return cur

def createMotionPath(curve_name, obj_name, node_name):
    u'''
    创建路径动画节点
    '''
    shapes = getShpe(curve_name)
    if not shapes:
        print(u"{} no shape node !!!".format(curve_name))
        return
    shape = shapes[0]
    motion_path_node = cmds.createNode("motionPath", n=node_name)
    shape_worldSpace_attr = "{}.{}".format(shape, NodeData.worldSpace)
    geometryPath_attr = "{}.geometryPath".format(motion_path_node)
    propertyConnectAttr(shape_worldSpace_attr, geometryPath_attr)
    propertyConnectAttr("{}.allCoordinates".format(motion_path_node), "{}.translate".format(obj_name))
    mel.eval('''setAttr "{}.fractionMode"(!false);'''.format(motion_path_node))
    return motion_path_node

def splineIkAdvTwist(spline_ik, upObject, forwardType=1):
    u'''
    线性ik高级扭曲相关设置
    '''
    cmds.setAttr("{}.dTwistControlEnable".format(spline_ik), 1)
    cmds.setAttr("{}.dWorldUpType".format(spline_ik), 3)
    propertyConnectAttr("{}.worldMatrix[0]".format(upObject), "{}.dWorldUpMatrix".format(spline_ik))
    cmds.setAttr("{}.dForwardAxis".format(spline_ik), forwardType)

def bezierCorner(path_curve):
    u'''
    为贝塞尔曲线添加贝塞尔角点
    '''
    cmds.select("{}.cv[*]".format(path_curve), r=True)
    cmds.BezierPresetBezierCorner()
    cmds.select(cl=True)

def duplicateJoint(root, prefix, suffix):
    u'''
    传入一个根关节即可
    复制一套骨骼，并且重名
    返回复制出来的骨骼列表
    '''
    copy_root = noNamesakeDuplicate(root)
    copy_joint_lst = getJointLstByRoot(copy_root)
    new_joint_list = renameObjList(copy_joint_lst, prefix, suffix)
    return new_joint_list

def concealObjects(name_lst, shape=True):
    u'''
    隐藏物体
    shape：隐藏的是否是形状节点
    '''
    if shape == True:
        lst = []
        for name in name_lst:
            lst += getShpe(name)
    else:
        lst = name_lst
    [cmds.setAttr("{}.visibility".format(obj), 0) for obj in lst]

def averageCons(startCon, endCon, beConLst, contype=0, andOne=False, skipType="none"):
    u'''
    平均约束被约束物体
    '''
    if andOne==True:
        averageValue = 1/(len(beConLst)+1)
    else:
        averageValue = 1/(len(beConLst)-1)
    parConLst = []
    for i in range(len(beConLst)):
        if andOne==False:
            next_value = i*averageValue
        else:
            next_value = (i+1)*averageValue
        first_value = 1 - next_value

        if contype == 0:
            con_node = cmds.parentConstraint(startCon, endCon, beConLst[i], mo=True)[0]
        elif contype == 1:
            con_node = cmds.pointConstraint(startCon, endCon, beConLst[i], mo=True, skip=skipType)[0]
        elif contype == 2:
            con_node = cmds.orientConstraint(startCon, endCon, beConLst[i], mo=True, skip=skipType)[0]
        elif contype == 3:
            con_node = cmds.scaleConstraint(startCon, endCon, beConLst[i], mo=True, skip=skipType)[0]
        cmds.setAttr("{}.{}W0".format(con_node, startCon), first_value)
        cmds.setAttr("{}.{}W1".format(con_node, endCon), next_value)
        parConLst.append(con_node)
    return parConLst

def createCurveByObjLst(obj_lst, degreeNum=1, curve_name=""):
    u'''
    通过传入的物体列表创建曲线
    '''
    point_pos = [cmds.xform(obj, ws=True, t=True, q=True) for obj in obj_lst]
    if curve_name == "":
        cur = cmds.curve(d=degreeNum, p=point_pos)
    else:
        cur = cmds.curve(n=curve_name, d=degreeNum, p=point_pos)
        curShape = cmds.listRelatives(cur, s=True)[0]
        cmds.rename(curShape, "{}_Shape".format(cur))
    return cur

def getJointLstByRoot(root_jnt):
    u'''
    通过根骨骼,获取骨骼链所有骨骼名称
    返回一个列表
    '''
    obj_lst = cmds.ls(cmds.listRelatives(root_jnt, ad=True), type="joint")
    assert isinstance(obj_lst, list)
    obj_lst.append(root_jnt)
    obj_lst.reverse()
    return obj_lst

def renameObjList(obj_list, prefix, suffix):
    u'''
    重命名一组物体
    obj_list: 物体列表
    name_format： 命名格式是 前缀_索引_后缀
    '''
    name_lst = []
    for i in range(len(obj_list)):
        new_name = "{}_{}_{}".format(prefix, i+1, suffix)
        cmds.rename(obj_list[i], new_name)
        name_lst.append(new_name)
    return name_lst

def conAttr(ctrols, ctroled, sttr, sttred):
    u'''
    属性链接功能，分别输入；控制者列表，驱动属性，被控制者列表，被驱动属性
    控制者对被控制者；适用于一对一，多对多，等比少对多，不等比少对多
    等比少对多，多数可以整除少数；不等比少对多，等比链接完之后，多余的被最后一个控制者控制
    '''
    sttrs = str('.{}'.format(sttr))
    sttreds = str('.{}'.format(sttred))

    index = int((len(ctroled)) / (len(ctrols)))
    for i in range(len(ctrols)):
        first_num = (0 + (i * index))
        next_num = (index + (i * index))

        for becons in ctroled[first_num:next_num]:
            cmds.connectAttr((ctrols[i] + sttrs), (becons + sttreds))

    if (len(ctroled)) / (len(ctrols)) != 0:
        end = int((len(ctrols)))
        endindex = end * index
        nextlist = ctroled[endindex:]
        for i in range(len(nextlist)):
            cmds.connectAttr((ctrols[-1] + sttrs), (nextlist[i] + sttreds))

def matchPos(obj_1, obj_2, match_type = 0):
    u'''
    将obj_2匹配至obj_1
    '''
    if match_type < 0 or match_type > 2:
        print(u"match type no legal !!!")
        return
    if match_type == 0:
        con_node = cmds.parentConstraint(obj_1, obj_2)
    elif match_type == 1:
        con_node = cmds.pointConstraint(obj_1, obj_2)
    elif match_type == 2:
        con_node = cmds.orientConstraint(obj_1, obj_2)
    cmds.delete(con_node)

def noNamesakeDuplicate(obj_name):
    u'''
    不会造成子集重名的复制功能
    '''
    mList = OpenMaya.MSelectionList()
    mList.add(obj_name)

    mObject = OpenMaya.MObject()
    mList.getDependNode(0, mObject)

    dagNode = OpenMaya.MFnDagNode(mObject)
    dp_object = dagNode.duplicate()

    dp_depend_node = OpenMaya.MFnDependencyNode(dp_object)
    return dp_depend_node.name()

def createCurveCluster(curName, grp=True, show=True):
    u'''
    曲线上每一个cv点创建一个簇
    '''
    cvLst = cmds.ls("{}.cv[*]".format(curName), fl=True)
    clusterLst = []
    for cv in range(len(cvLst)):
        clus = cmds.cluster(cvLst[cv], n="{}_{}_cluster".format(curName, cv+1))[1]
        if show == False:
            cmds.setAttr("{}.visibility".format(clus), 0)
        clusterLst.append(clus)
    if grp == True:
        cmds.group(clusterLst, n="{}_clusterGrp".format(curName))
    return clusterLst

def curveJoint(cur, jointNum):
    u'''
    曲线骨骼代码
    '''
    if not cmds.objExists(cur):
        return
    if jointNum <= 1:
        return
    curShapeList = cmds.listRelatives(cur, s=True)
    if not curShapeList:
        return
    curShape = curShapeList[0]
    parmer_value = (1.0 / (jointNum - 1))
    pointOnCurveNodeList = []
    jntList = []
    for i in range(jointNum):
        cmds.select(cl=True)
        jnt = cmds.joint(n="{}_joint_{}".format(cur, i + 1))
        jntList.append(jnt)
        pointCurveNode = cmds.createNode("pointOnCurveInfo")
        pointOnCurveNodeList.append(pointCurveNode)
        cmds.setAttr("{}.turnOnPercentage".format(pointCurveNode), 1)
        cmds.connectAttr("{}.worldSpace[0]".format(curShape), "{}.inputCurve".format(pointCurveNode))
        value = parmer_value * i
        cmds.setAttr("{}.parameter".format(pointCurveNode), value)
        cmds.connectAttr("{}.position".format(pointCurveNode), "{}.translate".format(jnt))
        cmds.disconnectAttr("{}.position".format(pointCurveNode), "{}.translate".format(jnt))
        if i > 0:
            cmds.parent("{}_joint_{}".format(cur, i + 1), "{}_joint_{}".format(cur, i))

    cmds.delete(pointOnCurveNodeList)
    cmds.joint(jntList[0], zso=1, ch=1, e=1, oj='xyz', secondaryAxisOrient='yup')
    cmds.joint(jntList[-1], zso=1, ch=1, e=1, oj='none')
    cmds.select(cl=True)
    return jntList

def reRootJnt(childJnt):
    u'''
    关节重定向
    '''
    cmds.select(childJnt, r=True)
    cmds.RerootSkeleton()
    return childJnt

def objZero(obj, clear=2):
    u'''
    将物体上的位移/旋转数值清零
    '''
    if clear > 2 or clear < 0:
        print(u"# type no legal !!!")
        return
    translate_attr = "{}.translate".format(obj)
    rotate_attr = "{}.rotate".format(obj)
    zero_lst = [0, 0, 0]
    if clear == 0:
        cmds.setAttr(translate_attr, *zero_lst)
    elif clear == 1:
        cmds.setAttr(rotate_attr, *zero_lst)
    elif clear == 2:
        cmds.setAttr(translate_attr, *zero_lst)
        cmds.setAttr(rotate_attr, *zero_lst)


def getExpContent(expNode):
    u'''
    获取表达式节点内容
    '''
    content = cmds.expression(expNode, s=True, q=True)
    return content

def editExpContent(expNode, expContent):
    u'''
    编辑表达式内容
    '''
    cmds.expression(expNode, s=expContent, e=True)

def createEXP(content, expName):
    u'''
    创建表达式
    '''
    exp_node = cmds.expression(s=content, ae=True, uc="all", n=expName)
    return exp_node

def isEx(obj):
    u'''
    判断物体是否存在
    '''
    return cmds.objExists(obj)

def node(node_name):
    u'''
    创建节点
    '''
    return cmds.createNode(node_name)

def getShpe(obj):
    u'''
    获取物体的形状节点
    '''
    return cmds.listRelatives(obj, s=True)

def getParent(obj):
    u'''
    获取父级
    '''
    par_lst = cmds.listRelatives(obj, p=True)
    if not par_lst:
        return []
    return par_lst

def isEx(obj):
    u'''
    判断物体是否存在
    '''
    return cmds.objExists(obj)

def hasAttr(obj, attr_name):
    u'''
    判断属性是否存在于物体上, 只需给出属性本名即可，无需带上物体名
    '''
    if attr_name in cmds.listAttr(obj):
        return True
    else:
        return False

def lockAttr(attr_name):
    u'''
    锁定属性, 该属性参数需要带上物体名称，即完整的属性名
    '''
    obj = attr_name.split(".")[0]
    attr = attr_name.split(".")[-1]
    if not isEx(obj):
        return
    if hasAttr(obj, attr):
        cmds.setAttr(attr_name, lock=True)

def getUperAttr(attr):
    u'''
    获取被链接属性的上游属性
    '''
    con_list = cmds.listConnections(attr, p=True)
    if con_list:
        return con_list
    else:
        return []

def disConnectAttr(coned_attr):
    u'''
    断开当前被链接的属性
    '''
    con_attr_list = getUperAttr(coned_attr)
    if con_attr_list:
        con_attr = con_attr_list[0]
        cmds.disconnectAttr(con_attr, coned_attr)

def propertyConnectAttr(con_attr, coned_attr):
    u'''
    特殊属性链接
    '''
    if con_attr not in getUperAttr(coned_attr):
        disConnectAttr(coned_attr)
        cmds.connectAttr(con_attr, coned_attr, f=True)


def sinExpContent(coned_grp_lst, same_coned_attr,
                  coned_ctrl_lst, ctrl_width_attr,
                  speed_attr, width_attr, go_attr, delay_attr, addWidth_attr):
    u'''
    正弦波浪表达式
    coned_grp_lst： 被控制的物体的组名称列表
    same_coned_attr: 被控制物体需要被控制的属性（短名称）
    coned_ctrl_lst: 控制的控制器名称列表
    ctrl_width_attr：每个控制器的幅度属性（短名称）
    speed_attr：主控制器的速度属性
    width_attr：主控制器的整体幅度属性
    go_attr：主控制器的手动偏移属性
    delay_attr: 主控制器的延迟属性
    addWidth_attr: 主控制器的局部幅度属性（幅度递减/递增属性）
    '''
    exp = ""
    for obj in range(len(coned_grp_lst)):
        attr = "{}.{}".format(coned_grp_lst[obj], same_coned_attr)
        ctrl_attr = "{}.{}".format(coned_ctrl_lst[obj], ctrl_width_attr)
        exp += "{} = sin(time * {} + {} - {} * {}) * {} * (1 + {} * {}) * {};\n".format(attr, speed_attr, go_attr, obj,
                                                                                        delay_attr, width_attr, obj,
                                                                                        addWidth_attr, ctrl_attr)
    return exp

def propertyParent(child, par):
    u'''
    特殊父子关系命令，尽可能保证不会报错
    '''
    if par not in getParent(child):
        cmds.parent(child, par)

def oneToOneParent(par_lst, child_lst):
    u'''
    两个物体列表，一对一的进行父子关系
    '''
    if len(par_lst) != len(child_lst):
        print(u"# list length no equal !!!")
        return
    for par, child in zip(par_lst, child_lst):
        if isEx(par) and isEx(child):
            propertyParent(child, par)

def eachParent(lst_1, lst_2):
    u'''
    交错父子关系
    '''
    for i, t in zip(lst_1, lst_2):
        i_index = lst_1.index(i)
        t_index = lst_2.index(t)
        cmds.parent(lst_2[t_index], lst_1[i_index])
        i_index += 1
        if i_index >= len(lst_1):
            continue
        cmds.parent(lst_1[i_index], lst_2[t_index])

def subExpContent(attr_lst, mode=0):
    u'''
    生成一个连续的表达式内容
    '''
    exp = ""
    if mode == 0:
        for attr in attr_lst:
            exp += "-{}".format(attr)
    elif mode == 1:
        for attr in attr_lst:
            exp += "+{}".format(attr)
    return exp

def bendExpContent(bendJointList, splineIkJointList, bendJntRotatedAttr, localBendAttr_lst, main_ctrl_bend_attr, main_ctrl_bendAgle_attr, main_ctrl_fallOff_attr, prefix):
    u'''
    尾巴/身体 卷曲表达式文本创建
    bendJointList：尾巴：需要卷曲的骨骼列表，列表内的骨骼顺序是从尾部末端骨骼到身体部分的开始骨骼  （其实就是一个反向的列表），身体：反之
    splineIkJointList: 尾巴：线性ik骨骼列表， 列表内的骨骼顺序是从尾部末端骨骼到身体部分的开始骨骼 （其实就是一个反向的列表），身体：反之
    bendJntRotatedAttr： 骨骼被控制的旋转轴属性 （rx/ry/rz）
    localBendAttr_lst: 局部弯曲控制属性的列表
    main_ctrl_bend_attr: 控制弯曲的主控制器属性
    main_ctrl_bendAgle_attr：主控制器的控制弯曲旋转数值范围的属性
    main_ctrl_fallOff_attr: 主控制器的弯曲衰减属性
    '''
    exp_node_lst = []
    bj_attr_lst = ["{}.{}".format(bj, bendJntRotatedAttr) for bj in bendJointList]
    spline_attr_lst = ["{}.{}".format(sj, bendJntRotatedAttr) for sj in splineIkJointList]
    for bj in bendJointList:
        index = bendJointList.index(bj)
        min_agle = "float $min = (-{}+({}*{}))*{} - {};\n".format(main_ctrl_bendAgle_attr, index, main_ctrl_fallOff_attr, localBendAttr_lst[index], spline_attr_lst[index])
        if_min = "if($min>0)$min=0;\n"
        max_agle = "float $max = ({}-({}*{}))*{} - {};\n".format(main_ctrl_bendAgle_attr, index, main_ctrl_fallOff_attr, localBendAttr_lst[index], spline_attr_lst[index])
        if_max = "if($max<0)$max=0;\n"
        tailExpContent = min_agle + max_agle + if_min + if_max
        if index == 0:
            tailExpContent += "{} = clamp($min, $max, {}*10);\n".format(bj_attr_lst[index],
                                                                   main_ctrl_bend_attr)
        else:
            attr_lst = bj_attr_lst[:index]
            temp_content = subExpContent(attr_lst)
            tailExpContent += "{} = clamp($min, $max, {}*10 {});\n".format(bj_attr_lst[index],
                                                                        main_ctrl_bend_attr, temp_content)
        exp_node = createEXP(tailExpContent, "{}_{}_{}_bendExp".format(prefix, bj, index))
        exp_node_lst.append(exp_node)
    return exp_node_lst

def hierarchy_conformity(lst_1, lst_2, lst_3):
    u'''
    蛇类骨骼绑定层级整合
    lst_1: B层骨骼列表
    lst_2： A层骨骼列表
    lst_3： fk控制器列表
    '''
    for i in lst_1:
        index = lst_1.index(i)
        cmds.parent(lst_2[index], lst_1[index])
        if index + 1 >= len(lst_1):
            continue
        cmds.parent(lst_1[index+1], lst_3[index])

def oneToOneConstraint(lst_1, lst_2, con_type=0, mo=True):
    u'''
    一对一进行约束
    '''
    if con_type > 3 or con_type < 0:
        print(u"# Constraint type no legal !!!")
        return
    if len(lst_1) != len(lst_2):
        print(u"# list length no equal !!!")
        return
    if mo == True:
        constraint_mo = True
    else:
        constraint_mo = False
    for i, t in zip(lst_1, lst_2):
        if con_type == 0:
            cmds.parentConstraint(i, t, mo=constraint_mo)
        elif con_type == 1:
            cmds.pointConstraint(i, t, mo=constraint_mo)
        elif con_type == 2:
            cmds.orientConstraint(i, t, mo=constraint_mo)
        elif con_type == 3:
            cmds.scaleConstraint(i, t, mo=constraint_mo)

def oneToOneConnectAttr(lst_1, lst_2, attr_name):
    u'''
    一对一属性链接
    '''
    if len(lst_1) != len(lst_2):
        print(u"# list length no equal !!!")
        return
    for i, t in zip(lst_1, lst_2):
        if hasAttr(i, attr_name) and hasAttr(t, attr_name):
            cmds.connectAttr("{}.{}".format(i, attr_name), "{}.{}".format(t, attr_name))

def giveGrpToObj(lst_1):
    u'''
    给物体打组，并且不破坏原有层级
    '''
    grp_node_lst = []
    for i in lst_1:
        grp_node = cmds.group(em=True, n="{}_GRP".format(i))
        cmds.delete(cmds.parentConstraint(i, grp_node))
        par_lst = getParent(i)
        cmds.parent(i, grp_node)
        if par_lst:
            cmds.parent(grp_node, par_lst[0])
        grp_node_lst.append(grp_node)
    return grp_node_lst

def constraint_allocation(con_1, con_2, coned, con_type=0, allocation_weight = 0.8):
    u'''
    约束分配，分配两个控制器对一个被控制器的约束权重
    '''
    if not isEx(con_2) or not isEx(con_1) or not isEx(coned):
        return
    if allocation_weight > 1.0 or allocation_weight < 0.0:
        return
    if con_type > 3 or con_type < 0:
        return
    if con_type == 0:
        con_node = cmds.parentConstraint(con_1, con_2, coned, mo=True)[0]
    elif con_type == 1:
        con_node = cmds.pointConstraint(con_1, con_2, coned, mo=True)[0]
    elif con_type == 2:
        con_node = cmds.orientConstraint(con_1, con_2, coned, mo=True)[0]
    elif con_type == 3:
        con_node = cmds.scaleConstraint(con_1, con_2, coned, mo=True)[0]

    second_weight = 1.0 - allocation_weight

    cmds.setAttr("{}.{}W0".format(con_node, con_1), allocation_weight)
    cmds.setAttr("{}.{}W1".format(con_node, con_2), second_weight)
    return con_node

def setConnectWeight(con_1,con_2,coned,attr="rx",value=0.8):
    u'''
    可设置控制权重的属性链接
    '''
    blendC_node = cmds.createNode("blendColors")
    cmds.setAttr("{}.blender".format(blendC_node), value)
    cmds.connectAttr("{}.{}".format(con_1, attr), "{}.color1R".format(blendC_node))
    cmds.connectAttr("{}.{}".format(con_2, attr), "{}.color2R".format(blendC_node))
    cmds.connectAttr("{}.outputR".format(blendC_node), "{}.{}".format(coned, attr))

def batchGradualConnect(con_1,con_2,coned_lst,attr="rx",addOne=True):
    u'''
    批量渐变属性链接
    '''
    con_length = len(coned_lst)
    if addOne == True:
        con_length += 1
    step_value = 1.0 / con_length
    for coned in range(len(coned_lst)):
        value = (1.0 - step_value * (coned+1))
        setConnectWeight(con_1, con_2, coned_lst[coned], attr, value)

def getSplineIkPathMaxOffsetValue(splineIkCurve):
    u'''
    获取线性ik的偏移值属性的最大值
    传入的参数是线性ik的曲线
    '''
    return cmds.getAttr("{}.maxValue".format(splineIkCurve))

def followPath(splinePathJointLst, ikCtrlGrpLst):
    u'''
    让ik控制器跟随线性ik的路径骨骼
    '''
    if len(splinePathJointLst) != len(ikCtrlGrpLst):
        print(u"# list length no equal !!!")
        return
    loc_lst = []
    for sj, ig in zip(splinePathJointLst, ikCtrlGrpLst):
        loc = cmds.spaceLocator(n="{}PosLoc".format(ig))[0]
        cmds.delete(cmds.parentConstraint(ig, loc))
        cmds.parentConstraint(loc, ig, mo=True)
        propertyParent(loc, sj)
        loc_lst.append(loc_lst)
    return loc_lst

def buildBodyFatScaleExp(coned_attrLst_sy, coned_attrLst_sz, fatSpeedAttr, fatGoAttr, fatDelayAttr, fatAttr, exp_name="snakeBodyScExp"):
    u'''
    创建骨骼正弦缩放绑定表达式
    '''
    exp_content = ""
    reverse_index_lst = [i for i in range(len(coned_attrLst_sy))]

    reverse_index_lst.reverse()
    for coned_attr in range(len(coned_attrLst_sy)):
        equal_content = pyCore.equalString([coned_attrLst_sy[coned_attr], coned_attrLst_sz[coned_attr]])
        content = "{} = sin(time*{} + {} + {}*{})*{} + {} + 1;\n".format(equal_content, fatSpeedAttr, fatGoAttr,
                                                                         reverse_index_lst[coned_attr], fatDelayAttr,
                                                                         fatAttr, fatAttr)
        exp_content += content

    createEXP(exp_content, exp_name)

def bodyWaveExp(fix_loc_lst, pointConstraint_lst, wave_loc, pos_loc, waveWidthAttr, index=1, exp_name="wave"):
    u'''
    身体波浪表达式创建
    fix_loc_lst: 蛇类身体绑定中，固定不动的定位器列表
    pointConstraint_lst：点约束节点列表
    wave_loc：被波浪控制器点约束的定位器 （也是使用这个定位器与固定不动的定位器对波浪定位器做点约束）
    pos_loc：固定在路径曲线上的波浪定位器
    waveWidthAttr：波浪定位器上控制波浪范围的属性
    index：固定定位器在点约束节点上的权重控制索引 （W0, W1。。。中的数字）
    '''
    for fix_loc, point_con in zip(fix_loc_lst, pointConstraint_lst):
        exp = "float $dis = mag(<<{0}.tx, {0}.ty, {0}.tz>> - <<{1}.tx, {1}.ty, {1}.tz>>) / {2};\n".format(pos_loc,
                                                                                                          fix_loc,
                                                                                                          waveWidthAttr)
        exp += "float $disR = smoothstep(0, 1, $dis);\n"
        exp += "{}.{}W{} = $disR;\n".format(point_con, fix_loc, index)
        exp += "{}.{}W{} = 1- $disR;\n".format(point_con, wave_loc, 1-index)
        createEXP(exp, exp_name)

def bodySliderScaleExp(joint_lst, fix_loc_lst, pos_loc, wave_ctrl):
    u'''
    身体波浪滑动缩放控制表达式（鼓包表达式）
    joint_lst： 波浪骨骼列表（在教程中叫 s_bWaveBn ）
    fix_loc_lst: 固定不动的定位器列表
    pos_loc: 固定在路径曲线上的波浪定位器
    wave_ctrl:波浪控制器
    '''
    for floc in fix_loc_lst:
        index = fix_loc_lst.index(floc)
        exp = "float $dis = mag(<<{0}.tx, {0}.ty, {0}.tz>> - <<{1}.tx, {1}.ty, {1}.tz>>) / {2}.sz;\n".format(pos_loc,
                                                                                                             floc,
                                                                                                             wave_ctrl)
        exp += "float $disR = 1 - smoothstep(0, 1, $dis);\n"
        exp += "{}.sy = 1 + $disR * ({}.sy - 1);\n".format(joint_lst[index], wave_ctrl)
        exp += "{}.sz = 1 + $disR * ({}.sx - 1);\n".format(joint_lst[index], wave_ctrl)
        createEXP(exp, "sliderScaleExp")

def setPlusNode(plus_name, index, value):
    u'''
    设置加减节点的属性值 input3D的属性值
    '''
    xyz_lst = ["x", "y", "z"]
    for xyz in xyz_lst:
        cmds.setAttr("{}.input3D[{}].input3D{}".format(plus_name, index, xyz), value)

def threeJointaScaleCombineToOneJoint(wave_joint_lst, fat_joint_lst, bind_joint_lst, bindBJTA_joint_lst):
    u'''
    三套关节缩放合并至一套关节上
    wave_joint_lst：波浪关节列表
    fat_joint_lst： 鼓包关节列表
    bind_joint_lst：bind关节列表
    bindBJTA_joint_lst： 蒙皮关节列表
    '''
    for wj, fj, bj, jta in zip(wave_joint_lst, fat_joint_lst, bind_joint_lst, bindBJTA_joint_lst):
        sub_plus_01_node = cmds.createNode("plusMinusAverage")
        cmds.setAttr("{}.operation".format(sub_plus_01_node), 2)
        cmds.connectAttr("{}.scale".format(wj), "{}.input3D[0]".format(sub_plus_01_node))
        setPlusNode(sub_plus_01_node, 1, 1)

        sub_plus_02_node = cmds.createNode("plusMinusAverage")
        cmds.setAttr("{}.operation".format(sub_plus_02_node), 2)
        cmds.connectAttr("{}.scale".format(fj), "{}.input3D[0]".format(sub_plus_02_node))
        setPlusNode(sub_plus_02_node, 1, 1)

        add_plus_01_node = cmds.createNode("plusMinusAverage")
        cmds.connectAttr("{}.scale".format(bj), "{}.input3D[0]".format(add_plus_01_node))
        cmds.connectAttr("{}.output3D".format(sub_plus_01_node), "{}.input3D[1]".format(add_plus_01_node))
        cmds.connectAttr("{}.output3D".format(sub_plus_02_node), "{}.input3D[2]".format(add_plus_01_node))

        cmds.connectAttr("{}.output3Dz".format(add_plus_01_node), "{}.scaleZ".format(jta))
        cmds.connectAttr("{}.output3Dy".format(add_plus_01_node), "{}.scaleY".format(jta))

def animContraintBodyJoint(joint_lst, fk_con_lst):
    u'''
    目标约束身体骨骼关节
    joint_lst：身体关节名称列表
    fk_con_lst：fk控制器名称列表
    '''
    for jnt in joint_lst:
        index = joint_lst.index(jnt)
        if index + 1 >= len(joint_lst):
            continue
        next_jnt = joint_lst[index+1]
        cmds.aimConstraint(next_jnt, jnt, mo=True, weight=1, aimVector=[1, 0, 0],
                           upVector=[0, 1, 0], worldUpType="objectrotation",
                           worldUpVector=[0, 1, 0], worldUpObject=fk_con_lst[index], skip="x")

def setJointScaleCompensateZero(jnt_lst, value=0):
    u'''
    将骨骼的分段比例补偿属性关闭
    传入一个骨骼名称列表
    需要将bind骨骼以及脖子及其以上骨骼的比例补偿关闭
    '''
    for jnt in jnt_lst:
        if cmds.nodeType(jnt) == u"joint":
            cmds.setAttr("{}.segmentScaleCompensate".format(jnt), value)


def wingExp(lst, rotate_axis, wing_degree, wing_speed, wing_go, wing_Delay):
    u'''
    摆动表达式 （类似于魔鬼鱼游泳时的那种摆动）
    lst: 被控制的物体的名称列表
    rotate_axis：被控制的旋转轴向
    wing_degree：摆动角度 属性
    wing_speed： 摆动速度 属性
    wing_go：手动摆动 属性
    wing_Delay：摆动延迟 属性

    如果要左右两边对应的物体摆动运动一致， 那么就先做一边，再做另外一边
    如果不需要一致， 那么可以将所有物体列表传入
    '''
    exp = ""
    for i in lst:
        attr = "{}.{}".format(i, rotate_axis)
        exp += "{} = sin(time * {} + {} - {}*{})*{};\n".format(attr, wing_speed, wing_go,
                                                               wing_Delay, lst.index(i), wing_degree)
    createEXP(exp, "wing_exp")

class NodeData:
    u'''
    记录节点名称，以及节点相关属性名称
    '''
    condition = "condition"
    multyDivide = "multiplyDivide"
    curveInfo = "curveInfo"
    motionPath = "motionPath"

    translate = "translate"
    rotate = "rotate"
    scale = "scale"

    arcLength = "arcLength"

    operation = "operation"
    worldSpace = "worldSpace[0]"
    inputCurve = "inputCurve"

    input_attr = "input"
    output_attr = "output"
    outColor = "outColor"

    firstTerm = "firstTerm"
    secondTerm = "secondTerm"

    colorIfTrue = "colorIfTrue"
    colorIfFalse = "colorIfFalse"
