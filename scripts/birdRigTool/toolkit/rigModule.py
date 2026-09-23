# -*- coding: utf 8 -*-

import maya.mel as mel
import maya.cmds as cmds
from . import cmdAPI

class RigData:
    u'''
    存储/记录 插件生成的相关节点
    '''
    noMoveGrp = "BIRDRIGTOOL_NOMVE_GROUP"      # 创建不可位移组
    follicleGrp = "BIRDRIGTOOL_FOLLICLE_GROUP" # 创建毛囊组
    curveGrp = "BIRDRIGTOOL_CURVE_GROUP"      # 创建曲线组
    posCurveLocGrp = "BIRDRIGTOOL_POSCURVELOC_GROUP" # 创建pos曲线的定位器组

    ikCurveAnimLocGrp = "BIRDRIGTOOL_IKCURVELOC_GROUP" # 创建跟随ik曲线的羽毛目标约束定位器的组
    mainIkCtrlGrp = "BIRDRIGTOOL_IKCTRL_GROUP" # 创建ik主要控制器的组
    clusterGrp = "BIRDRIGTOOL_CLUSTER_GROUP" # 创建放置所有簇的组
    ikGrp = "BIRDRIGTOOL_IKHANDLE_GROUP" # 创建所有线性ik的组
    subikCtrlGrp = "BIRDRIGTOOL_SUBIKCTRL_GROUP"  # 创建所有中间部分次级线性ik控制器的组


    allGrpLst = [follicleGrp, noMoveGrp, curveGrp, posCurveLocGrp, ikCurveAnimLocGrp, mainIkCtrlGrp, clusterGrp, ikGrp, subikCtrlGrp] # 所有组的列表

    follicleLst = []  # 驱动面片上的毛囊列表

    childJntXposData = {}  # 羽毛根骨骼x轴方向原本的数值

    guideJntLst = []  # 导航骨骼

    driverPeoCurLst = []  # 驱动面片和跟随曲线
    driverMesh = None  # 驱动面片
    driverCurve = None  # 驱动曲线

    allCurveLst = []  # 绑定中所有的曲线列表

    posCurveLocLst = []  # pos曲线上（点数少的曲线）的定位器列表（被tangent曲线控制的定位器）

    jntTanPosLocData = {}  # 每根羽毛骨骼对应的两个切线定位器 Tan，Pos

    ikCurveAnimLocLst = []  # ik曲线 目标定位器列表

    ikCtrlData = {}  # ik曲线的ik控制器的相关信息
    dynCtrlData = {}  # 动力学曲线的ik控制器的相关信息

    subSkinJntData = {} # 次级蒙皮关节信息

    rootRoateData = {"rootRotateX":"rx", "rootRotateY":"ry", "rootRotateZ":"rz"}
    rotRotateData = {"rotX":"rx", "rotY":"ry", "rotZ":"rz"}

    allIKFKJntData = {}  # 所有IKFK骨骼的信息

    ikAnimLocationData = {}  # ik目标定位器相关信息

    splineIkCurveData = {}  # 动力学线性Ik曲线相关信息
    splineIkCurveLst = []  # 动力学线性Ik曲线列表

    DynNodeData = {}  # 动力学节点相关信息

    splineCurveClusterData = {}  # 线性ik曲线簇列表的相关信息

    DYN_ctrl_curve = "BIRDRIGTOOL_DYN_CTRL"  # 动力学总控制器

    EXP_node_name = "BIRDRIGTOOL_DYN_EXPNode"  # 实时动力学表达式节点名称

    subikCtrlLst = []  # 次级ik控制器（参与动力学解算）

    mainFkCtrlShapeLst = []  # 所有fk控制器的形状节点列表，除了每根羽毛最末端的fk控制器的形状
    allEndFkCtrlLst = []  # 所有羽毛的最末端fk控制器列表

    BirdRigToolDynNodeGroup = 'BirdRigToolDynNodeGroup'

    all_dyn_ctrl_lst = []

def concealGrp():
    u'''
    隐藏各个绑定组
    '''
    for grp in RigData.allGrpLst:
        if grp == "BIRDRIGTOOL_SUBIKCTRL_GROUP" or grp == "BIRDRIGTOOL_IKCTRL_GROUP":
            continue
        cmds.setAttr("{}.v".format(grp), 0)


def addDynDriverAttr(ctrl):
    u'''
    添加动力学控制属性
    '''
    cmds.select(ctrl, r=True)
    if not cmdAPI.attrIsEx("open", ctrl):
        cmds.addAttr(ctrl, ln="open", at="bool",dv=1, k=True)

    if not cmdAPI.attrIsEx("startFrame", ctrl):
        cmds.addAttr(ctrl, ln="startFrame", at="long", dv=1, k=True)

    if not cmdAPI.attrIsEx("startCurveAttract", ctrl):
        cmds.addAttr(ctrl, ln="startCurveAttract", at="double",dv=0.1, k=True)

    if not cmdAPI.attrIsEx("motionDrag", ctrl):
        cmds.addAttr(ctrl, ln="motionDrag", at="double", dv=0.5, k=True)

    if not cmdAPI.attrIsEx("ctime", ctrl):
        cmds.addAttr(ctrl, ln="ctime", at="double", dv=0, k=True)

    if not cmdAPI.attrIsEx("playStyle", ctrl):
        cmds.addAttr(ln="playStyle",at="enum",en="autoDyn:realtimeDyn:",k=True)

    if not cmdAPI.attrIsEx("subIkVis", ctrl):
        cmds.addAttr(ctrl, ln="subIkVis", at="bool", dv=0, k=True)

    if not cmdAPI.attrIsEx("featherFkVis", ctrl):
        cmds.addAttr(ctrl, ln="featherFkVis", at="bool", dv=0, k=True)

    if not cmdAPI.attrIsEx("featherIkVis", ctrl):
        cmds.addAttr(ctrl, ln="featherIkVis", at="bool", dv=0, k=True)

def propertyParent(child, par):
    u'''
    特殊p成父子关系
    '''
    if par not in cmdAPI.getParent(child):
        cmds.parent(child, par)

def createGrp():
    for grpName in RigData.allGrpLst: 
        if not cmds.objExists(grpName):
            cmds.group(em=True, n=grpName) 

def createDynCtrl():
    u'''
    创建动力学控制器
    '''
    if not cmds.objExists(RigData.DYN_ctrl_curve):
        cmds.circle(n=RigData.DYN_ctrl_curve,nr=[0,1,0], ch=False, r=10)
        addDynDriverAttr(RigData.DYN_ctrl_curve)
        cmds.color(RigData.DYN_ctrl_curve, rgb=[1,0,0])

def createChainJnt(jntName):
    u'''
    创建一段骨骼
    '''
    cmds.select(cl=True)
    baseJnt = cmds.joint(n=jntName, p=(0,0,0))
    cmds.select(cl=True)
    endJnt = cmds.joint(n="{}_END".format(jntName), p=(0,0,-5))
    cmds.parent(endJnt, baseJnt)
    cmds.joint(baseJnt,e=True,oj="xyz",secondaryAxisOrient="yup",ch=True,zso=True)
    return baseJnt 

def createGuideJnt(jntLst, side="L"):
    u'''
    创建导航骨骼, 默认是左侧
    jntLst:鸟类臂膀骨骼列表
    '''
    copyJntLst = []
    for jntIndex in range(len(jntLst)):
        cmds.select(cl=True)
        jnt = cmds.joint(n="{}_{}_BIRDRIGTOOLCOPY".format(side, jntLst[jntIndex]))
        copyJntLst.append(jnt)
        cmds.delete(cmds.parentConstraint(jntLst[jntIndex], jnt))
        cmds.makeIdentity(jnt, apply=True)
        if jntIndex > 0:
            cmds.parent(jnt, "{}_{}_BIRDRIGTOOLCOPY".format(side, jntLst[jntIndex-1]))
    cmds.select(copyJntLst[-1], r=True)
    cmds.RerootSkeleton()

    cmds.joint(copyJntLst[-1],e=True,oj="xyz",secondaryAxisOrient="yup",ch=True,zso=True)
    
    guideJntLst = []
    for jnt, copyJnt in zip(jntLst[1:], copyJntLst[1:]):
        guideJnt = createChainJnt("{}_BIRDRIGTOOL_GUIDE_{}".format(side,jnt))
        cmds.delete(cmds.parentConstraint(jnt, copyJnt, guideJnt))
        guideJntLst.append(guideJnt)
    cmds.delete(copyJntLst)
    return guideJntLst 

def createDriverGeo(handJntLst,jntLst, guideJntLst, peoName="test"):
    u'''
    创建驱动面片,返回驱动面片和面片驱动的曲线

    handJntLst：鸟类臂膀骨骼列表（含肩胛骨）
    jntLst：鸟类羽毛骨骼列表
    guideJntLst：导航骨骼列表
    peoName：面片的名称
    '''
    driver_peo = cmds.polyPlane(n=peoName,w=1,h=1,sx=len(handJntLst),sy=1,ax=(0,1,0),cuv=2,ch=False)[0]
    peoVtxLst = cmds.ls("{}.vtx[*]".format(driver_peo), fl=True)
    
    firstLst = handJntLst + cmds.listRelatives(jntLst[-1], c=True)
    nextLst = cmds.listRelatives(jntLst[0], c=True) + [cmds.listRelatives(i, c=True)[0] for i in guideJntLst]
    
    firstVtx = peoVtxLst[:len(handJntLst)+1]
    nextVtx = peoVtxLst[len(handJntLst)+1:]
    
    for vtx, jnt in zip(firstVtx, firstLst):
        pos = cmds.xform(jnt, ws=True, t=True, q=True)
        cmds.xform(vtx, ws=True, t=pos)
    
    n = 0    
    for index in range(len(nextVtx)):
        if index <= len(nextLst)-1:
            pos = cmds.xform(nextLst[index], ws=True, t=True, q=True)
            cmds.xform(nextVtx[index], ws=True, t=pos)
            n += 1
    for vtx in nextVtx[n:]:
        pos = cmds.xform(nextLst[-1], ws=True, t=True, q=True)
        cmds.xform(vtx, ws=True, t=pos)
    
    combineVtxLst = nextVtx[n-1:]
    lostVtxLst = combineVtxLst[1:]    
    cmds.select(combineVtxLst, r=True)
    cmds.polyMergeVertex()
    cmds.select(driver_peo, r=True)
    cmds.polyAutoProjection()
    cmds.polyTriangulate()
    cmds.select(driver_peo, r=True)
    cmds.DeleteHistory()    
    backEdgeVtxLst = [i for i in nextVtx if i not in lostVtxLst] + [firstVtx[-1]]

    #cmds.delete(guideJntLst)

    cmdAPI.getLineEdgeByVtxs(backEdgeVtxLst, True)
    curve = cmds.polyToCurve(form=2,degree=1,conformToSmoothMeshPreview=1, n="{}_CURVE".format(driver_peo))[0]

    skinNode = cmds.skinCluster(handJntLst, driver_peo, tsb=True)[0]
    cmds.setAttr("{}.skinningMethod".format(skinNode), 1)
    cmds.setAttr("{}.normalizeWeights".format(skinNode), 2)
    return [driver_peo, curve]

def resetJntPos(cur, featherJntLst):
    u'''
    重新设置骨骼位置，让骨骼尽可能贴近曲线
    '''
    curshape = cmds.listRelatives(cur, s=True)[0]
    for childJnt in featherJntLst:
        rowY = cmds.getAttr("{}.ty".format(childJnt))
        rowZ = cmds.getAttr("{}.tz".format(childJnt))
        loc = cmds.spaceLocator()[0]
        loc2 = cmds.spaceLocator()[0]
        near = cmds.createNode("nearestPointOnCurve")
        cmds.delete(cmds.parentConstraint(childJnt, loc))
        cmds.connectAttr("{}.worldSpace[0]".format(curshape),"{}.inputCurve".format(near))
        cmds.connectAttr("{}.translate".format(loc),"{}.inPosition".format(near))
        cmds.connectAttr("{}.position".format(near),"{}.translate".format(loc2))
        cmds.delete(cmds.pointConstraint(loc2, childJnt))
        cmds.setAttr("{}.ty".format(childJnt),rowY)
        cmds.setAttr("{}.tz".format(childJnt),rowZ)
        cmds.delete(near, loc, loc2)

def reConnectRotate(conNode, beConNode):
    u'''
    重新链接约束与被链接物体的旋转
    '''
    plusLst = []
    XValue = cmds.getAttr("{}.rx".format(beConNode)) * -1
    YValue = cmds.getAttr("{}.ry".format(beConNode)) * -1
    ZValue = cmds.getAttr("{}.rz".format(beConNode)) * -1
    cmds.disconnectAttr("{}.constraintRotateX".format(conNode),"{}.rotateX".format(beConNode))
    cmds.disconnectAttr("{}.constraintRotateY".format(conNode),"{}.rotateY".format(beConNode))
    cmds.disconnectAttr("{}.constraintRotateZ".format(conNode),"{}.rotateZ".format(beConNode))
    plus = cmds.createNode("plusMinusAverage", n="{}_reConnectPlus".format(beConNode))
    cmds.connectAttr("{}.constraintRotate".format(conNode), "{}.input3D[0]".format(plus))
    cmds.setAttr("{}.input3D[1].input3Dx".format(plus), XValue)
    cmds.setAttr("{}.input3D[1].input3Dy".format(plus), YValue)
    cmds.setAttr("{}.input3D[1].input3Dz".format(plus), ZValue)
    cmds.connectAttr("{}.output3D".format(plus),"{}.rotate".format(beConNode))
    plusLst.append(plus)
    return plusLst

def createSubJnt(base_name, value):
    u'''
    创建次级骨骼链
    '''
    subjntLst = []
    for i in range(value):
        cmds.select(cl=True)
        jnt = cmds.joint(n="{}_{}_SubJnt".format(base_name, i+1), p=[0,0,i*-1])
        if i > 0:
            cmds.parent(jnt, "{}_{}_SubJnt".format(base_name, i))
        subjntLst.append(jnt)
    cmds.joint(subjntLst[0],e=True,oj="xyz",secondaryAxisOrient="yup",ch=True,zso=True) 
    cmds.joint(subjntLst[-1],e=True,oj="none",ch=True,zso=True) 
    return subjntLst 

def addRotateAttr(obj):
    u'''
    添加旋转控制属性
    '''
    attrLst = ["rootRotateX", "rootRotateY", "rootRotateZ", "rotX", "rotY", "rotZ"]
    allAttrLst = cmds.listAttr(obj)
    for attr in attrLst:
        if attr in allAttrLst:
            continue
        cmds.addAttr(obj,ln=attr,at="double",dv=0,k=True)  

class RigFeather:
    u'''
    翅膀绑定
    '''
    def __init__(self, handJntLst, featherJntLst, skinJntNum = 5, side="L"):
        u'''
        handJntLst: 鸟类手臂主要骨骼列表
        featherJntLst: 鸟类羽毛骨骼列表
        skinJntNum:每根羽毛蒙皮骨骼数量
        side: 辨别羽毛是在左边还是右边
        '''
        self.handJntLst = handJntLst
        self.featherJntLst = featherJntLst
        self.skinJntNum = skinJntNum

        self.handLstLength = len(self.handJntLst)
        self.featherJntLength = len(self.featherJntLst)

        self.splitNum = int(self.featherJntLength / self.handLstLength)

        self.side = side

        self.featherChildJntLst = [cmds.listRelatives(jnt, c=True)[0] for jnt in self.featherJntLst]

        self.JntPcData = dict(zip(self.featherChildJntLst,self.featherJntLst))  # 子骨骼为键，父骨骼为值， 为了方便后面子级骨骼找父级

        
    def parentJoint(self):
        u'''
        将羽毛骨骼 p 到鸟类手臂骨骼下 
        '''
        num = self.handLstLength-1
        endSplitNum = self.splitNum*num
        for node in self.featherJntLst[endSplitNum:]:
            if not cmds.listRelatives(node, p=True):
                cmds.parent(node, self.handJntLst[-1])

        for jntIndex in range(len(self.handJntLst)):
            firstNum = jntIndex *  self.splitNum
            nextNum = (jntIndex *  self.splitNum) + self.splitNum
            for jnt in self.featherJntLst[firstNum:nextNum]:
                if not cmds.listRelatives(node, p=True):
                    cmds.parent(jnt, self.handJntLst[jntIndex])
    
    def buildGuideJnt(self):
        u'''
        创建导航骨骼
        '''
        guideJntLst = createGuideJnt(self.handJntLst, self.side)
        RigData.guideJntLst = guideJntLst
        return guideJntLst

    def buildDriverGeo(self):
        u'''
        创建驱动曲面和曲线
        '''
        name_list = cmds.ls("{}_*_BIRDRIGTOOL_DRIVER_MESH".format(self.side))
        if not name_list:
            name_lenth = 0
        else:
            name_lenth = len(name_list)+1
        mesh_name = "{}_{}_BIRDRIGTOOL_DRIVER_MESH".format(self.side, name_lenth)
        driverPeoCurLst = createDriverGeo(self.handJntLst, self.featherJntLst, RigData.guideJntLst, mesh_name)
        RigData.driverPeoCurLst = driverPeoCurLst
        RigData.driverMesh = driverPeoCurLst[0]
        RigData.driverCurve = driverPeoCurLst[1]
        return driverPeoCurLst 

    def buldFollicle(self):
        u'''
        创建毛囊用于点约束羽毛骨骼
        让羽毛钉在驱动曲面上
        '''
        follicleLst = cmdAPI.createFollicleOnMesh(RigData.driverMesh, self.featherJntLst, conType=1, parentNode=RigData.follicleGrp)
        RigData.follicleLst = follicleLst
        return follicleLst

    def firstSetOutline(self):
        u'''
        第一次整理层级
        '''
        propertyParent(RigData.driverMesh, RigData.noMoveGrp)
        propertyParent(RigData.driverCurve, RigData.curveGrp)
        propertyParent(RigData.curveGrp, RigData.noMoveGrp)    
        propertyParent(RigData.follicleGrp, RigData.noMoveGrp)

    def buldResidueAllCurves(self):
        u'''
        创建剩余的所有曲线
        返回所有的曲线列表
        '''  
        IKCurve = cmds.duplicate(RigData.driverCurve, n="{}_IK".format(RigData.driverCurve))[0]  # 创建IK曲线
        DYNCurve = cmds.duplicate(RigData.driverCurve, n="{}_DYN".format(RigData.driverCurve))[0] # 创建动力学曲线

        tangent_name_list = cmds.ls("{}_*_TANGENT_CURVE".format(self.side))
        if not tangent_name_list:
            name_lenth = 0
        else:
            name_lenth = len(tangent_name_list)+1
        tangent_name = "{}_{}_TANGENT_CURVE".format(self.side, name_lenth)
        tangentCur = cmdAPI.createCurveByObjLst(self.featherJntLst, degreeNum=3, curve_name=tangent_name) # 根据羽毛骨骼生成切线曲线
        posCurve = cmds.duplicate(tangentCur, rr=True, n="{}_POS".format(tangentCur))[0] # 生成Pos曲线
        cmds.rebuildCurve(posCurve, ch=0, rpo=1, rt=0, end=1, kr=0, kcp=0, kep=1, kt=0, s=4, d=3, tol=0.01)
        propertyParent(tangentCur, RigData.curveGrp)
        propertyParent(posCurve, RigData.curveGrp)
        curveLst = [RigData.driverCurve, IKCurve, DYNCurve, tangentCur, posCurve] # 曲线列表
        RigData.allCurveLst = curveLst
        return curveLst

    def buildPosCurveLoc(self):
        u'''
        创建Pos曲线上的定位器控制
        '''
        locLst = cmdAPI.createCurveLocCtrl(RigData.allCurveLst[-1], locNameFormat="_Locator")
        cmdAPI.locatorLockOnCurve(RigData.allCurveLst[-2], locLst)
        RigData.posCurveLocLst = locLst
        cmds.parent(locLst, RigData.posCurveLocGrp)
        return locLst
    
    def saveJntLenthData(self):
        u'''
        存储骨骼长度信息
        同时让末端的骨骼尽可能贴近曲线
        '''
        lenthData = {}
        for sub_jnt in self.featherChildJntLst:
            xValue = cmds.getAttr("{}.tx".format(sub_jnt))
            data = {self.JntPcData[sub_jnt]:xValue}
            lenthData.update(data)
        RigData.childJntXposData = lenthData
        resetJntPos(RigData.allCurveLst[2], self.featherChildJntLst)
        return lenthData

    def createTanPosLocator(self):
        u'''
        创建切线定位器
        Tan和Pos两个定位器,并且打一个组放入到每根羽毛骨骼的父级骨骼中
        '''
        tanPosMainData = {}
        for jnt, fol in zip(self.featherJntLst,RigData.follicleLst):
            tanLoc = cmds.spaceLocator(n="{}_Tan".format(jnt))[0]
            posLoc = cmds.spaceLocator(n="{}_Pos".format(jnt))[0]
            cmds.delete(cmds.parentConstraint(jnt, tanLoc))
            cmds.delete(cmds.parentConstraint(jnt, posLoc))
            grp = cmds.group(tanLoc, posLoc, n="{}_TanPosLocGrp".format(jnt))
            cmds.setAttr("{}.v".format(grp), 0)
            parentNode = cmds.listRelatives(jnt, p=True)[0]
            cmds.parent(grp, parentNode)
            cmds.pointConstraint(fol, tanLoc, mo=True)
            cmds.pointConstraint(fol, posLoc, mo=True)
            data = {jnt:{"Tan":tanLoc, "Pos":posLoc}}
            cmds.select(RigData.allCurveLst[-1], r=True)
            cmds.select(posLoc, add=True)
            cmds.tangentConstraint(weight=1,aimVector=[0,0,1],upVector=[0,1,0],worldUpType="objectrotation",worldUpVector=[0,1,0],worldUpObject=tanLoc)
            tanPosMainData.update(data)
            cmds.select(cl=True)
        RigData.jntTanPosLocData = tanPosMainData
        return tanPosMainData
    
    def curveFollowRig(self):
        u'''
        cv点数多的那个曲线（tangent）跟随绑定
        '''
        tangentCurveCvLst = cmds.ls("{}.cv[:]".format(RigData.allCurveLst[-2]), fl=True)
        cv_indexLst = range(len(tangentCurveCvLst))
        cur_shape = cmds.listRelatives(RigData.allCurveLst[-2], s=True)[0]
        for cvIndex,jnt in zip(cv_indexLst, self.featherJntLst):
            tanLoc = RigData.jntTanPosLocData[jnt]["Tan"]
            locShape = cmds.listRelatives(tanLoc, s=True)[0]
            cmds.connectAttr("{}.worldPosition[0]".format(locShape), "{}.controlPoints[{}]".format(cur_shape, cvIndex))

    def jntAnimLocation(self):
        u'''
        创建关节目标定位器
        '''
        animLocLst = []
        for childJnt in self.featherChildJntLst:
            animLoc = cmds.spaceLocator(n="{}_CurveAnimLoc".format(childJnt))[0]
            cmds.delete(cmds.parentConstraint(childJnt, animLoc))
            animLocLst.append(animLoc)
        cmdAPI.locatorLockOnCurve(RigData.allCurveLst[1], animLocLst)

        for jnt, animLoc in zip(self.featherJntLst, animLocLst):
            PosLoc = RigData.jntTanPosLocData[jnt]["Pos"]
            animCNode = cmds.aimConstraint(animLoc,jnt,mo=1,
                                           aimVector=[1,0,0],
                                           upVector=[0,1,0],
                                           worldUpType="objectrotation",
                                           worldUpVector=[0,1,0],
                                           worldUpObject=PosLoc)[0] 
            cmds.select(cl=True)
        RigData.ikCurveAnimLocLst = animLocLst
        cmds.parent(animLocLst, RigData.ikCurveAnimLocGrp)
        propertyParent(RigData.ikCurveAnimLocGrp, RigData.posCurveLocGrp)
        return animLocLst
    
    def createIkCtrl(self):
        u'''
        创建ik曲线的控制器
        '''
        clustergrp = cmdAPI.createCurveCluster(RigData.allCurveLst[1])
        clusterLst = cmds.listRelatives(clustergrp, c=True)
        ikCtrlData = cmdAPI.createIkCtrl(clusterLst, 1.5, [0,0,1])
        RigData.ikCtrlData = ikCtrlData
        cmds.parent(ikCtrlData["conGrpALst"], RigData.mainIkCtrlGrp)
        cmds.parent(clustergrp, RigData.clusterGrp)
        cmdAPI.locatorLockOnCurve(RigData.driverCurve, ikCtrlData["conGrpALst"])
        return ikCtrlData
    
    def createDynCtrl(self):
        u'''
        创建动力学曲线的控制器
        '''
        clustergrp = cmdAPI.createCurveCluster(RigData.allCurveLst[2])
        clusterLst = cmds.listRelatives(clustergrp, c=True)
        dynCtrlData = cmdAPI.createIkCtrl(clusterLst, 1)
        cmds.parent(clustergrp, RigData.clusterGrp)
        for dynGrpA, ikctrl in zip(dynCtrlData["conGrpALst"], RigData.ikCtrlData["conLst"]):
            cmds.parent(dynGrpA, ikctrl)
        RigData.dynCtrlData = dynCtrlData
        return dynCtrlData
    
    def createSubJoints(self):
        u'''
        创建次级羽毛关节
        '''
        subSkinJntData = {}
        for jnt in self.featherJntLst:
            posValue = RigData.childJntXposData[jnt]
            everyPos = posValue / (self.skinJntNum-1)
            subJntLst = createSubJnt(jnt, self.skinJntNum)
            cmds.delete(cmds.parentConstraint(jnt, subJntLst[0]))
            cmds.makeIdentity(subJntLst[0], apply=True)
            cmds.parent(subJntLst[0], jnt)
            for sub_jnt in subJntLst[1:]:
                cmds.setAttr("{}.tx".format(sub_jnt), everyPos)
            data = {jnt:subJntLst}
            subSkinJntData.update(data)
        RigData.subSkinJntData = subSkinJntData
        return subSkinJntData

    def createIKFKJnt(self):
        u'''
        创建次级蒙皮关节ikfk骨骼
        '''
        allIkFkJntData = {}
        mainFkCtrlShapeLst = []
        allEndFkCtrlLst = []
        for jnt in self.featherJntLst:
            ikfkData = cmdAPI.CreateIKFKJnt(RigData.subSkinJntData[jnt][0]).main
            cmds.parent(ikfkData["FKJntLst"][0],jnt)
            cmds.parent(ikfkData["IKJntLst"][0],jnt)
            ctrlDataLst = cmdAPI.createFkInChain(ikfkData["FKJntLst"], 2)
            data = {jnt:ikfkData}
            allIkFkJntData.update(data)
            for ik, fk, skin in zip(ikfkData["IKJntLst"], ikfkData["FKJntLst"], RigData.subSkinJntData[jnt]):
                cmds.connectAttr("{}.t".format(ik), "{}.t".format(fk))
                cmds.connectAttr("{}.r".format(ik), "{}.r".format(fk))
                cmds.connectAttr("{}.s".format(ik), "{}.s".format(fk))
                cmds.parentConstraint(fk, skin, mo=True)

            curveLst = ctrlDataLst[0]
            for cur in curveLst[:-1]:
                mainFkCtrlShapeLst += cmds.listRelatives(cur, s=True)

            allEndFkCtrlLst.append(curveLst[-1])

            addRotateAttr(curveLst[-1])
            for rootAttr, rotateAttr in RigData.rootRoateData.items():
                cmds.connectAttr("{}.{}".format(curveLst[-1], rootAttr), "{}.{}".format(ctrlDataLst[1][curveLst[0]][0], rotateAttr))

            for rotAttr, rotateAttr in RigData.rotRotateData.items():
                for ctrl in curveLst:
                    cmds.connectAttr("{}.{}".format(curveLst[-1], rotAttr), "{}.{}".format(ctrlDataLst[1][ctrl][1], rotateAttr))
        
        RigData.allIKFKJntData = allIkFkJntData
        RigData.mainFkCtrlShapeLst = mainFkCtrlShapeLst
        RigData.allEndFkCtrlLst = allEndFkCtrlLst
        return allIkFkJntData
    
    def subIkLocation(self):
        u'''
        次级ik目标定位
        '''
        ikAnimLocationData = {}
        locBLst = []
        locALst = []
        for childJnt in self.featherChildJntLst:
            parJnt = self.JntPcData[childJnt]
            locA = cmds.spaceLocator(n="{}_A_LOC".format(parJnt))[0]
            locB = cmds.spaceLocator(n="{}_B_LOC".format(parJnt))[0]
            locAGrp = cmds.group(locA, n="{}_GROUP".format(locA))
            cmds.setAttr("{}.v".format(locAGrp), 0)
            cmds.delete(cmds.pointConstraint(childJnt, locAGrp))
            cmds.delete(cmds.pointConstraint(childJnt, locB))
            cmds.parent(locAGrp, parJnt)
            locBLst.append(locB)
            locALst.append(locA)
            data = {parJnt:{"locB":locB, "locA":locA}}
            ikAnimLocationData.update(data)
        cmdAPI.locatorLockOnCurve(RigData.allCurveLst[2], locBLst)
        for locb, loca in zip(locBLst, locALst):
            cmds.pointConstraint(locb, loca, mo=True)
        cmds.parent(locBLst, RigData.ikCurveAnimLocGrp)

        RigData.ikAnimLocationData = ikAnimLocationData
        return ikAnimLocationData

    def createSplineIkCurve(self):
        u'''
        创建线性ik曲线, 并且创建簇变形绑定
        ''' 
        splineIkCurveData = {}
        splineIkCurveLst = []
        splineCurveClusterData = {}
        subikCtrlLst = []
        for jnt in self.featherJntLst:
            ikjntLst = RigData.allIKFKJntData[jnt]["IKJntLst"]
            cur = cmdAPI.createCurveByObjLst(ikjntLst, 1, "{}_IK_CURVE".format(jnt))
            splineIkCurveLst.append(cur)
            data = {jnt:cur}
            splineIkCurveData.update(data)
            curClusterGrp = cmdAPI.createCurveCluster(cur)
            clusetrLst = cmds.listRelatives(curClusterGrp, c=True)
            cData = {jnt:clusetrLst}
            splineCurveClusterData.update(cData)
            cmds.parent(clusetrLst[:2], jnt)
            for ikc in clusetrLst[:2]:
                cmds.setAttr("{}.v".format(ikc),0)

            ikgrpDta = cmdAPI.createIkCtrl(clusetrLst[2:], rValue=0.5, rgbLst=[1,1,0])
            cmds.setAttr("{}.scale".format(ikgrpDta["conLst"][-1]), 1.5,1.5,1.5)
            cmds.makeIdentity(ikgrpDta["conLst"][-1], apply=True, s=True)

            subikCtrlLst.append(ikgrpDta["conLst"][-1])
            propertyParent(curClusterGrp, RigData.ikCurveAnimLocGrp)
            animGrp = ikgrpDta["conGrpALst"][-1]
            animCNode = cmds.aimConstraint(jnt, animGrp,
                                           aimVector=[1,0,0],
                                           upVector=[0,1,0],
                                           worldUpType="objectrotation",
                                           worldUpVector=[0,1,0],
                                           worldUpObject=RigData.jntTanPosLocData[jnt]["Pos"])[0] 
            
            cmdAPI.averageCons(clusetrLst[1], ikgrpDta["conLst"][-1], ikgrpDta["conGrpALst"][:-1], True)
            for mid in ikgrpDta["conGrpALst"][:-1]:
                cmds.setAttr("{}.v".format(mid), 0)

            ikFollowLoc = cmds.spaceLocator(n="{}_FollowLocator".format(ikgrpDta["conLst"][-1]))[0]
            cmds.delete(cmds.parentConstraint(ikgrpDta["conLst"][-1], ikFollowLoc))
            cmds.parent(ikFollowLoc, RigData.ikAnimLocationData[jnt]["locA"])
            cmds.pointConstraint(ikFollowLoc, ikgrpDta["conGrpALst"][-1], mo=True)
            cmds.parent(ikgrpDta["conGrpALst"], RigData.subikCtrlGrp)
            
        RigData.splineCurveClusterData = splineCurveClusterData
        RigData.splineIkCurveData = splineIkCurveData
        RigData.splineIkCurveLst = splineIkCurveLst
        RigData.subikCtrlLst = subikCtrlLst
        return [splineIkCurveLst,splineIkCurveData]

    def dynIkCurve(self):
        u'''
        动力学化选定曲线，并且整理动力学节点
        '''
        data = cmdAPI.Dyn(RigData.splineIkCurveLst).main
        RigData.DynNodeData = data
        dynCurveGrp = data["dynNodeLst"][1]
        curveLst = cmds.listRelatives(dynCurveGrp, c=True)
        ikLst = []
        for dynCur, jnt in zip(curveLst, self.featherJntLst):
            ikJntLst = RigData.allIKFKJntData[jnt]["IKJntLst"]
            ik = cmdAPI.createSplineIK(ikJntLst[0], ikJntLst[-1], dynCur)
            ikLst.append(ik)
        cmds.parent(ikLst, RigData.ikGrp)
        propertyParent(RigData.ikGrp, data["dynGrp"])

        hairShapeNode = cmds.listRelatives(data["dynNodeLst"][2], s=True)[0]

        cmdAPI.DynSwitch(RigData.splineIkCurveLst, curveLst, "{}.open".format(RigData.DYN_ctrl_curve), hairShapeNode).doIt
        
        dynNodeLst = [hairShapeNode, data["dynNodeLst"][-1]]
        ctrl_lst = RigData.ikCtrlData["conLst"]+RigData.dynCtrlData["conLst"]+RigData.subikCtrlLst+self.handJntLst

        RigData.all_dyn_ctrl_lst += ctrl_lst
        #cmdAPI.createRealTimeExp(RigData.DYN_ctrl_curve, ctrl_lst, dynNodeLst, RigData.EXP_node_name)  # !!!!!!!

        dynCtrlAttr_startCurveAttract = "{}.startCurveAttract".format(RigData.DYN_ctrl_curve)
        dynNodeAttr_startCurveAttract = "{}.startCurveAttract".format(hairShapeNode)
        dynCtrlAttr_motionDrag = "{}.motionDrag".format(RigData.DYN_ctrl_curve)
        dynNodeAttr_motionDrag = "{}.motionDrag".format(hairShapeNode)

        cmds.connectAttr(dynCtrlAttr_startCurveAttract, dynNodeAttr_startCurveAttract)
        cmds.connectAttr(dynCtrlAttr_motionDrag, dynNodeAttr_motionDrag)
    
    def endParent(self):
        u'''
        最后的大纲整理
        '''
        propertyParent(RigData.posCurveLocGrp, RigData.noMoveGrp)
        propertyParent(RigData.BirdRigToolDynNodeGroup, RigData.noMoveGrp)
        propertyParent(RigData.clusterGrp, RigData.noMoveGrp)

    def linkVisAttr(self):
        u'''
        链接可见性/并且设置最末端fk控制器大小
        '''
        ctrlFkVis = "{}.featherFkVis".format(RigData.DYN_ctrl_curve)
        for shape in RigData.mainFkCtrlShapeLst:
            cmds.connectAttr(ctrlFkVis, "{}.visibility".format(shape))
            
        subIkVisCtrlAttr = "{}.subIkVis".format(RigData.DYN_ctrl_curve)
        subIkGrpVis = "{}.visibility".format(RigData.subikCtrlGrp)
        
        if subIkVisCtrlAttr not in cmdAPI.isConnect(subIkGrpVis):
            cmds.connectAttr(subIkVisCtrlAttr, subIkGrpVis)

        ctrlIkVis = "{}.featherIkVis".format(RigData.DYN_ctrl_curve)
        ikCtrlGrpA = RigData.ikCtrlData["conGrpALst"][-1]
        cmds.connectAttr(ctrlIkVis, "{}.visibility".format(ikCtrlGrpA))

        value = 2.0
        for ctrl in RigData.allEndFkCtrlLst:
            cmds.setAttr("{}.scale".format(ctrl), value, value, value)
            cmds.makeIdentity(ctrl, apply=True, s=True)

    def doIt(self):
        u'''
        执行绑定
        '''

        # common part
        #self.parentJoint()
        createGrp()
        createDynCtrl()
        self.buildDriverGeo()
        self.buldFollicle()
        self.firstSetOutline()
        self.buldResidueAllCurves()
        self.buildPosCurveLoc()
        self.saveJntLenthData()
        self.createTanPosLocator()
        self.curveFollowRig()
        self.jntAnimLocation()
        self.createIkCtrl()
        self.createDynCtrl()
        self.createSubJoints()
        self.createIKFKJnt()

        # DYN part
        self.subIkLocation()
        self.createSplineIkCurve()
        self.dynIkCurve()

        # endParent
        self.endParent()

        #Link vis
        self.linkVisAttr()

def realTimeDynExp():
    u'''
    最终的实时动力学表达式
    '''
    main_ctrl = RigData.DYN_ctrl_curve
    ctrl_lst = [i for i in RigData.all_dyn_ctrl_lst if cmdAPI.isEx(i)]
    nucleus_node = cmds.ls(cmds.listRelatives(RigData.BirdRigToolDynNodeGroup, ad=True), type="nucleus")[0]
    hair_shape_lst = cmds.ls(cmds.listRelatives(RigData.BirdRigToolDynNodeGroup, ad=True), type="hairSystem")
    cmdAPI.endRealTimeExp(main_ctrl, ctrl_lst, nucleus_node, hair_shape_lst, RigData.EXP_node_name)

def buildRig(handRootJnt, handJntLst, featherJntLst,side="L",skinJntNum=5,mirro=True):
    
    if mirro == True:
        if side == "L":
            cmds.mirrorJoint(handRootJnt,mirrorYZ=True,mirrorBehavior=True,searchReplace=["L_","R_"])[0]
            RigFeather(handJntLst, featherJntLst,skinJntNum = skinJntNum, side=side).doIt()
            newGuideLst = []
            for guideJnt in RigData.guideJntLst:
                newGuideJnt = cmds.mirrorJoint(guideJnt,mirrorYZ=True,mirrorBehavior=True,searchReplace=["L_","R_"])[0]
                newGuideLst.append(newGuideJnt)
            cmds.delete(RigData.guideJntLst)
            RigData.guideJntLst = newGuideLst
            newFeatherJntLst = [i.replace("L_", "R_") for i in featherJntLst]
            newHandJntLst = [i.replace("L_", "R_") for i in handJntLst]
            RigFeather(newHandJntLst, newFeatherJntLst,skinJntNum = skinJntNum, side="R").doIt()
            cmds.delete(RigData.guideJntLst)
        if side == "R":
            cmds.mirrorJoint(handRootJnt,mirrorYZ=True,mirrorBehavior=True,searchReplace=["R_","L_"])[0]
            RigFeather(handJntLst, featherJntLst,skinJntNum = skinJntNum, side=side).doIt()
            newGuideLst = []
            for guideJnt in RigData.guideJntLst:
                newGuideJnt = cmds.mirrorJoint(guideJnt,mirrorYZ=True,mirrorBehavior=True,searchReplace=["R_","L_"])[0]
                newGuideLst.append(newGuideJnt)
            cmds.delete(RigData.guideJntLst)
            RigData.guideJntLst = newGuideLst
            newFeatherJntLst = [i.replace("R_","L_") for i in featherJntLst]
            newHandJntLst = [i.replace("R_","L_") for i in handJntLst]
            RigFeather(newHandJntLst, newFeatherJntLst,skinJntNum = skinJntNum, side="L").doIt()
            cmds.delete(RigData.guideJntLst)
            
    else:
        RigFeather(handJntLst, featherJntLst,skinJntNum = skinJntNum, side=side).doIt()
        cmds.delete(RigData.guideJntLst)

    concealGrp()

    realTimeDynExp()