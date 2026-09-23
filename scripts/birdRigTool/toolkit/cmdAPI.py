# -*- coding: utf 8 -*-
import os
import maya.mel as mel
import maya.cmds as cmds
import maya.OpenMaya as OpenMaya

def importFile(path):
    u'''
    导入骨骼
    '''
    if not os.path.exists(path):
        return
    mel.eval('''file -import -type "mayaAscii"  -ignoreVersion
                -ra true -mergeNamespacesOnClash true -namespace ":"
                -options "v=0;"  -pr  -importTimeRange "combine" "{}";'''.format(path))

def autoParent(lst_1, lst_2):
    u'''
    自动父子关系
    '''
    if not lst_1 or not lst_2:
        return
    lst_1_len = len(lst_1)
    lst_2_len = len(lst_2)
    if lst_1_len > lst_2_len:
        for i in range(lst_2_len):
            if cmds.listRelatives(lst_2[i], p=True) == None or lst_1[i] not in cmds.listRelatives(lst_2[i], p=True):
                cmds.parent(lst_2[i], lst_1[i])
        return 
    value = int(lst_2_len / lst_1_len)
    temp_length = value * lst_1_len
    if temp_length < lst_2_len:
        moreNum = lst_2_len - temp_length
        for childNum in range(lst_1_len):
            firstSplitNum = childNum*value
            if childNum == lst_1_len-1:
                nextSplitNum = ((childNum+1)*value)+moreNum
            else:
                nextSplitNum = ((childNum+1)*value)
            nowSplitChildLst = lst_2[firstSplitNum:nextSplitNum]
            for child in nowSplitChildLst:
                if cmds.listRelatives(child, p=True) == None or lst_1[childNum] not in cmds.listRelatives(child, p=True):
                    cmds.parent(child, lst_1[childNum])

    elif temp_length == lst_2_len:
        for childNum in range(lst_1_len):
            firstSplitNum = childNum*value
            nextSplitNum = (childNum+1)*value
            nowSplitChildLst = lst_2[firstSplitNum:nextSplitNum]
            for child in nowSplitChildLst:
                if cmds.listRelatives(child, p=True) == None or lst_1[childNum] not in cmds.listRelatives(child, p=True):
                    cmds.parent(child, lst_1[childNum])

    cmds.select(cl=True)

def cubeCtrl(ctrlName, value=0.25):
    u'''
    立方体曲线
    '''
    ctrl = mel.eval('''curve -n {} -d 1
                    -p 1 1 1
                    -p 1 1 -1
                    -p -1 1 -1
                    -p -1 1 1
                    -p 1 1 1
                    -p 1 -1 1
                    -p 1 -1 -1
                    -p 1 1 -1
                    -p -1 1 -1
                    -p -1 -1 -1
                    -p 1 -1 -1
                    -p 1 -1 1
                    -p -1 -1 1
                    -p -1 -1 -1
                    -p -1 -1 1
                    -p -1 1 1
                    -k 0 -k 1 -k 2 -k 3
                    -k 4 -k 5 -k 6 -k 7
                    -k 8 -k 9 -k 10 -k 11
                    -k 12 -k 13 -k 14 -k 15 ;'''.format(ctrlName))
    cmds.setAttr("{}.scale".format(ctrl), value,value,value)
    cmds.makeIdentity(ctrl, apply=True)
    return ctrl

def reRootJnt(childJnt):
    u'''
    关节重定向
    '''
    cmds.select(childJnt, r=True)
    cmds.RerootSkeleton()
    return childJnt 

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

def getPosition(obj):
    u'''
    获取物体的世界空间位置列表（点线面等也可以）
    '''
    return cmds.xform(obj, q=True, a=True, t=True, ws=True)

def insert_joint(root_jnt, pos):
    u'''
    插入骨骼，输入根骨骼，再输入插入骨骼的坐标
    即可在目标位置生成插入骨骼
    '''
    insert_jnt = cmds.insertJoint(root_jnt)
    cmds.joint(insert_jnt, e=True, co=True, p=pos)
    return insert_jnt

def getChildren2(obj):
    u'''
    获取对象子集
    '''
    if len(cmds.listRelatives(obj, c=True, type='transform')) == 1:
        return cmds.listRelatives(obj, c=True, type='transform')[0]
    return cmds.listRelatives(obj, c=True, type='transform')

def insert_jnt_cmd(root_jnt_list, insert_number):
    u'''
    插入自定义数量骨骼命令
    '''
    if insert_number < 1:
        return
    if not root_jnt_list:
        return
    for root in root_jnt_list:
        sub_jnt = getChildren2(root)
        if not sub_jnt:
            continue
        start_pos = getPosition(root)
        end_pos = getPosition(sub_jnt)
        all_insert_pos_list = get_mid_pos(start_pos, end_pos, insert_number)
        all_insert_pos_list.reverse()
        for pos in all_insert_pos_list:
            insert_joint(root, pos)

def reverCur(cur, axis = 0):
    u'''
    反转曲线
    '''
    cvLst = cmds.ls("{}.cv[*]".format(cur), fl=True)
    sPos = cmds.xform(cvLst[0], ws=True, t=True, q=True)[axis]
    ePos = cmds.xform(cvLst[-1], ws=True, t=True, q=True)[axis]
    if  sPos < ePos:
        cmds.reverseCurve(cur, ch=False, rpo=True)

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
    parmer_value = (1.0 / (jointNum-1))
    pointOnCurveNodeList = []
    jntList = []
    for i in range(jointNum):
        cmds.select(cl=True)
        jnt = cmds.joint(n="{}_joint_{}".format(cur, i+1))
        jntList.append(jnt)
        pointCurveNode = cmds.createNode("pointOnCurveInfo")
        pointOnCurveNodeList.append(pointCurveNode)
        cmds.setAttr("{}.turnOnPercentage".format(pointCurveNode), 1)
        cmds.connectAttr("{}.worldSpace[0]".format(curShape), "{}.inputCurve".format(pointCurveNode))
        value = parmer_value * i
        cmds.setAttr("{}.parameter".format(pointCurveNode),value)
        cmds.connectAttr("{}.position".format(pointCurveNode), "{}.translate".format(jnt))
        cmds.disconnectAttr("{}.position".format(pointCurveNode), "{}.translate".format(jnt))
        if i > 0:
            cmds.parent("{}_joint_{}".format(cur, i+1),"{}_joint_{}".format(cur, i))
        
    cmds.delete(pointOnCurveNodeList)
    cmds.joint(jntList[0], zso=1, ch=1, e=1, oj='xyz', secondaryAxisOrient='yup')
    cmds.joint(jntList[-1], zso=1, ch=1, e=1, oj='none')
    cmds.select(cl=True)
    return jntList         
        
def getLineEdgeByVtxs(vtx_lst, r=False):
    u'''
    获取一组连续顶点的所形成的边
    '''
    cmds.select(vtx_lst,r=True)
    mel.eval('''PolySelectConvert 2;''')
    edgeLst = cmds.ls(sl=True, fl=True)
    realEdgeLst = []
    for edge in edgeLst:
        cmds.select(edge,r=True)
        mel.eval('''PolySelectConvert 3;''')
        pointLst = cmds.ls(sl=True, fl=True)
        usefulPoint = []
        for p in pointLst:
            if p in vtx_lst:
                usefulPoint.append(p)
        if len(usefulPoint) == 2:
            realEdgeLst.append(edge)
    if r == True:
        cmds.select(realEdgeLst)
    else:
        cmds.select(cl=True)
    return realEdgeLst 

def getChildrenLstByLst(objLst):
    u'''
    获取一组物体的子级物体列表
    '''
    childLst = []
    for jnt in objLst:
        childLst += getChildren(jnt)
    return childLst

def createCurveCluster(curName):
    u'''
    曲线上每一个cv点创建一个簇
    '''
    cvLst = cmds.ls("{}.cv[*]".format(curName), fl=True)
    clusterLst = []
    for cv in range(len(cvLst)):
        clus = cmds.cluster(cvLst[cv], n="{}_{}_cluster".format(curName, cv+1))[1]
        clusterLst.append(clus)
    grp = cmds.group(clusterLst, n="{}_clusterGrp".format(curName))
    return grp

def ballCtrl(baseName, rValue=0.5):
    u'''
    创建球形控制器
    '''
    normalLst = [[1,0,0], [0,1,0], [0,0,1]]
    ctrlLst = []
    for nor in range(len(normalLst)):
        ctrl = cmds.circle(n = "{}_{}_ctrl".format(baseName, nor+1),r=rValue, ch=False, normal=normalLst[nor])[0]
        ctrlLst.append(ctrl)
    for ctrl in ctrlLst[1:]:
        shape = cmds.listRelatives(ctrl, s=True)[0]
        cmds.parent(shape, ctrlLst[0], r=True, s=True)
    cmds.delete(ctrlLst[1:])
    cmds.select(cl=True)
    cmds.color(ctrlLst[0], rgb=(0,0,1))
    return ctrlLst[0]

def createJnt(jntName):
    u'''
    创建一个骨骼
    '''
    cmds.select(cl=True)
    jnt = cmds.joint(n=jntName)
    return jnt

def lstTolstConnectAttr(lst1, lst2):
    u'''
    两个列表中的元素一对一将位移旋转缩放链接
    '''
    transformAttrLst = ["t", "r", "s"]
    for ik, fk in zip(lst1, lst2):
        for attr in transformAttrLst:
            cmds.connectAttr("{}.{}".format(ik, attr), "{}.{}".format(fk, attr), f=True) 
    
class CreateIKFKJnt:
    u'''
    创建IKFK骨骼
    '''
    def __init__(self, root, childType="joint"):
        self.root = root
        self.childType = childType

    @property
    def getTypeLstByRoot(self):
        u'''
        通过一个根节点获取同一类型的子级列表
        '''
        childLst = cmds.listRelatives(self.root, ad=True, type=self.childType)
        childLst.append(self.root)
        childLst.reverse()
        return childLst

    def createSameJntChain(self, prefix="IK"):
        u'''
        创建一条相同的骨骼链，只是添加了前缀
        '''
        childJntLst = self.getTypeLstByRoot
        jnt_lst = []
        for jnt in range(len(childJntLst)):
            smae_jnt = createJnt("{}_{}_{}".format(prefix, jnt+1, childJntLst[jnt]))
            cmds.delete(cmds.parentConstraint(childJntLst[jnt], smae_jnt))
            cmds.makeIdentity(smae_jnt, apply=True)
            jnt_lst.append(smae_jnt)
            if jnt > 0:
                cmds.parent(smae_jnt, "{}_{}_{}".format(prefix, jnt, childJntLst[jnt-1]))
        return jnt_lst 
    
    @property
    def main(self):
        ikJntLst = self.createSameJntChain("IK")
        fkJntLst = self.createSameJntChain("FK")
        return {"IKJntLst":ikJntLst, "FKJntLst":fkJntLst}

def createSplineIK(rootJnt, endJnt, curName):
    u'''
    创建线性ik
    '''
    cmds.select(rootJnt, endJnt, r=True)
    cmds.select(curName, add=True)
    ikHandleNode = cmds.ikHandle(sol="ikSplineSolver", ccv=False, scv=False, pcv=False, n="{}_splineIkHandle".format(rootJnt))[0]
    cmds.select(cl=True)
    return ikHandleNode 

def get_farthest_vertices(obj):
    u'''
    获取模型上相距最远的两个顶点
    '''
    selection = OpenMaya.MSelectionList()
    selection.add(obj)
    dag_path = OpenMaya.MDagPath()
    selection.getDagPath(0, dag_path)

    vertex_iter = OpenMaya.MItMeshVertex(dag_path)

    max_distance_squared = 0.0
    farthest_vertices = []

    while not vertex_iter.isDone():
        current_vertex = vertex_iter.position(OpenMaya.MSpace.kWorld)
        
        inner_vertex_iter = OpenMaya.MItMeshVertex(dag_path)
        while not inner_vertex_iter.isDone():
            inner_vertex = inner_vertex_iter.position(OpenMaya.MSpace.kWorld)

            distance_squared = current_vertex.distanceTo(inner_vertex)
            
            if distance_squared > max_distance_squared:
                max_distance_squared = distance_squared
                farthest_vertices = [vertex_iter.index(), inner_vertex_iter.index()]

            inner_vertex_iter.next()

        vertex_iter.next()

    return farthest_vertices

def createJntByMeshVtxId(mesh, idLst,comPareAixs="Z",side="L", fk=True):
    u'''
    通过模型的点id，在模型对应点上创建骨骼
    '''
    aixsData = {"X":0,"Y":1,"Z":2}
    value = aixsData[comPareAixs]
    vtxPosLst = []
    jntLst = []
    
    for id in range(len(idLst)):
        vtx = "{}.vtx[{}]".format(mesh, idLst[id])
        vtxPos = cmds.xform(vtx, ws=True, t=True, q=True)
        vtxPosLst.append(vtxPos[value])
        cmds.select(cl=True)
        jnt = cmds.joint(n="{}_{}_{}_joint".format(side, mesh, id+1), p=vtxPos)
        jntLst.append(jnt)
    data = dict(zip(vtxPosLst, jntLst))
    vtxPosLst.sort()
    vtxPosLst.reverse()
    if fk != True:
        return jntLst
    for pos in range(len(vtxPosLst)):
        if pos > 0:
            vtx = vtxPosLst[pos]
            vtx_1 = vtxPosLst[pos-1]
            cmds.parent(data[vtx], data[vtx_1])
    rootJnt = data[vtxPosLst[0]]
    endJnt = data[vtxPosLst[-1]]
    cmds.joint(rootJnt,e=True,oj="xyz",secondaryAxisOrient="yup",ch=True,zso=True) 
    cmds.joint(endJnt,e=True,oj="none",ch=True,zso=True) 
    return rootJnt
  
def createJntByMesh(meshLst, aixs="Z", side="L"):
    u'''
    通过模型上最远的两个顶点创建骨骼
    '''
    for mesh in meshLst:
        if not cmds.objExists(mesh):
            continue
        vtxIndeLst = get_farthest_vertices(mesh)
        createJntByMeshVtxId(mesh, vtxIndeLst,comPareAixs=aixs,side=side,fk=True)

def isEx(obj):
    u'''
    判断物体是否存在
    '''
    return cmds.objExists(obj)

def attrIsEx(attrName, obj):
    u'''
    判断属性是否在物体上
    '''
    if attrName in cmds.listAttr(obj):
        return True
    else:
        return False

def isConnect(attr):
    u'''
    判断属性是否被链接
    '''
    lst = cmds.listConnections(attr, p=True)
    if not lst:
        return []
    return lst

def disConnectAttr(attrName):
    u'''
    断开属性链接
    '''
    con_attr_lst = cmds.listConnections(attrName, p=True, scn=True)
    if not con_attr_lst:
        return
    else:
        cmds.disconnectAttr(con_attr_lst[0], attrName)
        print(u"# disConnectAttr successful !!!")

def getParent(obj):
    u'''
    获取物体父级
    '''
    p_lst = cmds.listRelatives(obj, p=True)
    if not p_lst:
        return []
    return p_lst

def getChildren(obj):
    u'''
    获取子级
    '''
    c_lst = cmds.listRelatives(obj, c=True)
    if not c_lst:
        return []
    return c_lst

def getCurveCvNumber(cur_name, num=True):
    u'''
    获取曲线所有cv点/cv点数
    '''
    cv_lst = cmds.ls("{}.cv[:]".format(cur_name), fl=True)
    if num == True:
        return len(cv_lst)
    return cv_lst

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

def createFkCtrl(obj_lst):
    u'''
    创建老船方式的fk控制器
    '''
    ctrl_lst = []
    ctrlGrp_lst = []
    ctrlGrpA_lst = []
    rotAttr_data = {"rotx":"Rotx","roty":"Roty","rotz":"Rotz"}
    rotAttr_lst = list(rotAttr_data.keys())
    rotate_attr_lst = ["rx", "ry", "rz"]
        
    for obj_index in range(len(obj_lst)):
        ctrl = cmds.circle(n="{}Con".format(obj_lst[obj_index]), ch=False)[0]
        ctrl_lst.append(ctrl)
        ctrlGrp = cmds.group(ctrl, n="{}Grp".format(ctrl))
        ctrlGrp_lst.append(ctrlGrp)
        ctrlGrpA = cmds.group(ctrlGrp, n="{}A".format(ctrlGrp))
        ctrlGrpA_lst.append(ctrlGrpA)
        cmds.delete(cmds.parentConstraint(obj_lst[obj_index], ctrlGrpA))
        cmds.parentConstraint(ctrl, obj_lst[obj_index])
        if obj_index > 0:
            cmds.parent(ctrlGrpA, "{}Con".format(obj_lst[obj_index-1]))
            
    for rotAttr, rotAttrNn in rotAttr_data.items():
        cmds.addAttr(ctrl_lst[-1],ln=rotAttr, nn=rotAttrNn, at="double", dv=0, k=True)
    cmds.addAttr(ctrl_lst[-1], ln="showCon", at="bool", k=True, dv=1) 
           
    for ctrl in ctrl_lst[:-1]:
        ctrl_shape = cmds.listRelatives(ctrl, s=True)[0]
        cmds.connectAttr("{}.showCon".format(ctrl_lst[-1]), "{}.visibility".format(ctrl_shape))
    for conGrp in ctrlGrp_lst:
        for con_attr, rotate_attr in zip(rotAttr_lst, rotate_attr_lst):
            cmds.connectAttr("{}.{}".format(ctrl_lst[-1], con_attr), "{}.{}".format(conGrp, rotate_attr))
        
    return {"con":ctrl_lst, "conGrp":ctrlGrp_lst, "conGrpA":ctrlGrpA_lst}
        
def createIkCtrl(lst, rValue=0.25, rgbLst=[1,0,0]):
    u'''
    创建ik控制器
    '''
    con_lst = []
    conGrp_lst = []
    conGrpA_lst = []
    for obj in lst:
        conName = "{}Con".format(obj)
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
        cmds.parentConstraint(con, obj)
    return {"conLst":con_lst, "conGrpLst":conGrp_lst, "conGrpALst":conGrpA_lst}

def createFollicle(follicle_name, parentNode=None):
    u'''
    创建毛囊节点,
    指定父节点并且父节点存在时，将毛囊 p 进父节点 
    '''
    follicle_shape = cmds.createNode("follicle", n="{}Shape".format(follicle_name))
    follicle_transform = cmds.listRelatives(follicle_shape, p=True)[0]
    cmds.connectAttr("{}.outTranslate".format(follicle_shape), "{}.translate".format(follicle_transform))
    cmds.connectAttr("{}.outRotate".format(follicle_shape), "{}.rotate".format(follicle_transform))
    cmds.rename(follicle_transform, follicle_name)
    if parentNode and isEx(parentNode):
        cmds.parent(follicle_transform, parentNode)
    return {"shape":follicle_shape, "transform":follicle_transform}

def createFollicleOnMesh(mesh, obj_lst, conType=1, parentNode=None):
    u'''
    将毛囊创建在模型的指定的位置
    '''
    follicle_lst = []
    cpom_lst = []
    mesh_shape = cmds.listRelatives(mesh,s=True)[0]
    for obj in obj_lst:
        xform_pos = cmds.xform(obj, ws=True, t=True, q=True)
        cpom_name = "{}_cpom".format(obj)
        if not cmds.objExists(cpom_name):
            cpom_node = cmds.createNode("closestPointOnMesh", n=cpom_name)
            cmds.connectAttr("{}.worldMesh[0]".format(mesh_shape), "{}.inMesh".format(cpom_node))
        else:
            cpom_node = cpom_name
        cpom_lst.append(cpom_node)
        cmds.setAttr("{}.inPosition".format(cpom_node), *xform_pos)
        follicle_name = "{}_follicle".format(obj)
        if isEx(follicle_name):
            continue
        follicleData = createFollicle(follicle_name, parentNode)
        cmds.connectAttr("{}.outMesh".format(mesh_shape), "{}.inputMesh".format(follicleData["shape"]))
        cmds.connectAttr("{}.worldMatrix[0]".format(mesh_shape), "{}.inputWorldMatrix".format(follicleData["shape"]))
        follicle_lst.append(follicleData["transform"])
        cmds.connectAttr("{}.parameterU".format(cpom_node), "{}.parameterU".format(follicleData["shape"]))
        cmds.connectAttr("{}.parameterV".format(cpom_node), "{}.parameterV".format(follicleData["shape"]))
        if conType == 0:
            cmds.parentConstraint(follicleData["transform"], obj, mo=True)
        elif conType == 1:
            cmds.pointConstraint(follicleData["transform"], obj, mo=True)
        elif conType == 2:
            cmds.orientConstraint(follicleData["transform"], obj, mo=True)   
        elif conType == 3:
            cmds.scaleConstraint(follicleData["transform"], obj, mo=True)      
    cmds.delete(cpom_lst)
    return follicle_lst

def createCurveLocCtrl(curve_name, locNameFormat="_locator_ctrl"):
    u'''
    生成控制曲线顶点的定位器控制
    '''
    if not isEx(curve_name):
        return
    locator_lst = []
    cur_shape = cmds.listRelatives(curve_name, s=True)[0]
    cur_cv_lst = cmds.ls("{}.cv[:]".format(curve_name), fl=True)
    for point_index in range(len(cur_cv_lst)):
        locNmae = "{}_{}{}".format(curve_name, point_index, locNameFormat)
        if isEx(locNmae):
            continue
        loc = cmds.spaceLocator(n=locNmae)[0]
        loc_shape = cmds.listRelatives(loc, s=True)[0]
        pos = cmds.xform(cur_cv_lst[point_index], ws=True, t=True, q=True)
        cmds.setAttr("{}.translate".format(loc), *pos)
        cmds.connectAttr("{}.worldPosition[0]".format(loc_shape), "{}.controlPoints[{}]".format(cur_shape, point_index))
        locator_lst.append(loc)
    return locator_lst

def locatorLockOnCurve(cur, loc_lst):
    u'''
    将定位器锁定在曲线上，不会改变定位器原有位置
    注意：需要确保定位器没有偏移组，导致定位器真正的位移数值与世界位置数值不符
    '''
    if not isEx(cur):
        return
    cur_shape = cmds.listRelatives(cur, s=True)[0]
    pocInfo_node_lst = []
    for loc in loc_lst:
        npoc_node = cmds.createNode("nearestPointOnCurve", n="{}_npoc".format(loc))
        pocInfo_node = cmds.createNode("pointOnCurveInfo", n="{}_pocInfo".format(loc))
        pocInfo_node_lst.append(pocInfo_node)
        loc_translate_lst = cmds.getAttr("{}.translate".format(loc))[0]
        cmds.connectAttr("{}.worldSpace[0]".format(cur_shape), "{}.inputCurve".format(npoc_node))
        cmds.setAttr("{}.inPosition".format(npoc_node), *loc_translate_lst)
        result_value = cmds.getAttr("{}.parameter".format(npoc_node))
        cmds.delete(npoc_node)
        cmds.setAttr("{}.parameter".format(pocInfo_node), result_value)
        cmds.connectAttr("{}.worldSpace[0]".format(cur_shape), "{}.inputCurve".format(pocInfo_node))
        cmds.connectAttr("{}.position".format(pocInfo_node), "{}.translate".format(loc))
    return pocInfo_node_lst

class CurControlCur:
    u'''
    cv点数多的曲线控制cv点少的曲线
    '''
    def __init__(self, cur_name_1, cur_name_2, locator_name_format="_locator_ctrl"):

        if getCurveCvNumber(cur_name_1) > getCurveCvNumber(cur_name_2):
            self.cur_name_1 = cur_name_1
            self.cur_name_2 = cur_name_2
        else:
            self.cur_name_1 = cur_name_2
            self.cur_name_2 = cur_name_1
        self.locator_name_format = locator_name_format

    @property
    def createLowCurveControl(self):
        u'''
        创建cv点少的曲线的定位器控制
        '''
        return createCurveLocCtrl(self.cur_name_2, self.locator_name_format)

    @property
    def main(self):
        u'''
        通过定位器，使cv点多的曲线控制cv点少的曲线
        '''
        locator_lst = self.createLowCurveControl
        if not locator_lst:
            return
        pointInfo_lst = locatorLockOnCurve(self.cur_name_1, locator_lst)
        return {"Locator":locator_lst, "pointOncurveInfo":pointInfo_lst}

def AB_hierarchy(aJntLst, bJntLst):
    u'''
    A层fk骨骼与B层fk骨骼层级关系
    '''
    for a, b in zip(aJntLst, bJntLst):
        cmds.parent(b, a)

class HairAttr:
    currentTime = "currentTime"

    motionDrag = "motionDrag"
    startCurveAttract = "startCurveAttract"
    startFarme = "startFarme"

    dynAttrLst = ["currentTime", "motionDrag"]
    dynOpen = "dynOpen"

class Dyn:
    def __init__(self, curve_lst, dynGrpName='BirdRigToolDynNodeGroup'):
        self.curve_lst = curve_lst
        self.dynGrpName = dynGrpName
    
    @property
    def makeDyn(self):
        u'''
        动力学化选定曲线
        '''
        cmds.select(self.curve_lst, r=True)
        mel.eval(''' makeCurvesDynamic 2 { "1", "0", "1", "1", "0"}; ''')
        for cur in self.curve_lst:
            cur_shape = cmds.listRelatives(cur, s=True)[0]
            cmds.setAttr("{}.intermediateObject".format(cur_shape), 0)

    @property
    def getObjDynNodeLst(self):
        u'''
        获取动力学化选定曲线的动力学节点
        '''
        follicleShape_attr = cmds.listConnections("{}.worldMatrix[0]".format(self.curve_lst[0]), p=True)[0]
        follicleShape = follicleShape_attr.split(".")[0]
        cmds.setAttr("{}.pointLock".format(follicleShape), 1)
        follicleNode = cmds.listConnections("{}.worldMatrix[0]".format(self.curve_lst[0]))[0]
        dynCurveNode = cmds.listConnections("{}.outCurve".format(follicleShape))[0]

        follicleGrp = cmds.listRelatives(follicleNode, p=True)[0]
        dynCurveGrp = cmds.listRelatives(dynCurveNode, p=True)[0]
        hairSystemNode = cmds.listConnections("{}.currentPosition".format(follicleShape))[0]
        nucleusNode = cmds.listConnections("{}.nextState".format(cmds.listRelatives(hairSystemNode, s=True)[0]))[0]
        for cur in self.curve_lst:
            folicle = cmds.listRelatives(cur, p=True)[0]
            folicle_shape = cmds.listRelatives(folicle, s=True)[0]
            cmds.setAttr("{}.pointLock".format(folicle_shape) , 1)

        return [follicleGrp, dynCurveGrp, hairSystemNode, nucleusNode]
    
    @property
    def main(self):
        self.makeDyn
        node_lst = self.getObjDynNodeLst
        if not isEx(self.dynGrpName):
            grp = cmds.group(node_lst, n=self.dynGrpName)
        else:
            grp = self.dynGrpName
            [cmds.parent(node, self.dynGrpName) for node in node_lst if self.dynGrpName not in getParent(node)]
        return {"dynGrp":grp, "dynNodeLst":node_lst}

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

def createRealTimeText(obj_lst, propertyAttrLst=["rotx", "roty", "rotz"]):
    u'''
    创建实时动力学表达式文本内容
    '''
    trs_lst = ["t", "r", "s"]
    xyz_lst = ["x", "y", "z"]
    attr_lst = []
    for trs in trs_lst:
        for xyz in xyz_lst:
            attr_name = "{}{}".format(trs, xyz)
            attr_lst.append(attr_name)
                   
    exp = "float $dyn;\n"
    for obj in obj_lst:
        obj_allAttr_lst = cmds.listAttr(obj)
        temp_lst = [p_attr for p_attr in propertyAttrLst if p_attr in obj_allAttr_lst]
        loop_lst = attr_lst + temp_lst
        for attr in loop_lst:
            exp += "$dyn = {}.{};\n".format(obj, attr)
    exp += "// BIRD_RIGTOOL_SPLIT_STR //\n"
    return exp

def createDynNodeText(control, dynLst):
    u'''
    创建动力学相关节点（nucleus/hairSystem等）的表达式文本
    '''
    for dynNode in dynLst:
        for dynAttr in HairAttr.dynAttrLst:
            if attrIsEx(dynAttr, dynNode):
                disConnectAttr("{}.{}".format(dynNode, dynAttr))
    
    exp = '''
if(frame<={0}.startFarme){1}.currentTime=1;
else
{1}.currentTime += 1;
{2}.currentTime = {1}.currentTime;
'''.format(control, dynLst[1], dynLst[0])
    return exp
    
def createEXP(content, expName):
    u'''
    创建表达式
    '''
    exp_node = cmds.expression(s=content, ae=True, uc="all", n=expName)
    return exp_node

def endRealTimeExp(main_ctrl, ctrl_lst, nucleus_node, hair_shape_lst, exp_name):
    for dynNode in hair_shape_lst:
        for dynAttr in HairAttr.dynAttrLst:
            if attrIsEx(dynAttr, dynNode):
                disConnectAttr("{}.{}".format(dynNode, dynAttr))
    disConnectAttr("{}.{}".format(nucleus_node, HairAttr.currentTime))
    if isEx(exp_name):
        cmds.delete(exp_name)
    first_content = createRealTimeText(ctrl_lst)


    next_content = '''
float $autotime=time1.outTime;
if(frame<={0}.startFrame){0}.ctime=$autotime;
else
{0}.ctime+=1;\n
if({0}.playStyle==0){1}.currentTime=$autotime;
else
{1}.currentTime={0}.ctime;
{1}.startFrame={0}.startFrame;\n
'''.format(main_ctrl, nucleus_node)

    print(next_content)

    third_content = ""
    for hair in hair_shape_lst:
        cmds.connectAttr("{}.motionDrag".format(main_ctrl), "{}.motionDrag".format(hair))
        third_content += \
"{}.currentTime = {}.currentTime;\n".format(hair, nucleus_node)
    exp_content = next_content + first_content + third_content
    createEXP(exp_content, exp_name)


class DynSwitch:
    u'''
    动力学开关
    '''
    def __init__(self, startCurveLst, outPutCurveLst, conAttr, hairSystemNode):
        self.startCurveLst = startCurveLst
        self.outPutCurveLst = outPutCurveLst
        self.conAttr = conAttr
        self.hairSystemNode = hairSystemNode

    @property
    def reverseConnectCurveBs(self):
        u'''
        开始曲线列表中的曲线给输出曲线列表中的曲线做bs，
        控制器属性conAttr通过一个反转节点链接bs目标体
        最后将用于动力学开始曲线与动力学输出曲线做融合变形
        '''
        bs_lst = []
        reverseNode = cmds.createNode("reverse", n="Dyn_Reverse")
        cmds.connectAttr(self.conAttr, "{}.inputX".format(reverseNode))
        for cur_1, cur_2 in zip(self.startCurveLst, self.outPutCurveLst):
            bs_node = cmds.blendShape(cur_1, cur_2, n="{}_BS".format(cur_2))[0]
            cmds.connectAttr("{}.outputX".format(reverseNode), "{}.{}".format(bs_node, cur_1))
            bs_lst.append(bs_node)
        return {"bsNodeLst":bs_lst, "reverseNode":reverseNode}
    
    @property
    def linkHairSystemSimulationMethond(self):
        u'''
        链接毛发系统的解算方式属性
        '''
        Condition = cmds.createNode("condition", n="{}_SimulationCondition".format(self.hairSystemNode))
        cmds.setAttr("{}.colorIfTrueR".format(Condition), 1)
        cmds.setAttr("{}.colorIfFalseR".format(Condition), 3)
        cmds.connectAttr(self.conAttr, "{}.firstTerm".format(Condition))
        cmds.connectAttr("{}.outColorR".format(Condition), "{}.simulationMethod".format(self.hairSystemNode))
        return Condition 
    
    @property
    def doIt(self):
        self.reverseConnectCurveBs
        self.linkHairSystemSimulationMethond

def createFkInChain(fk_lst, grpNum=0):
    u''''
    在骨骼单链中，创建fk控制器
    grpNum是控制器的组的数量
    '''
    resultData = {}

    data = {}
    for i in fk_lst:
        child = cmds.listRelatives(i, c=True)
        if not child:
            sub_data = {i:[]} 
        else:
            sub_data = {i:child[0]}
        data.update(sub_data)

    curLst = []
    for i in range(len(fk_lst)):
        cur = ballCtrl(fk_lst[i])
        curLst.append(cur)
        if grpNum == 0:
            beConObj = cur
            grp_data = {cur:[]}
        else:
            parGrp = []
            for num in range(grpNum):
                grp = cmds.group(cur, n="{}_{}_grp".format(cur, num+1))
                parGrp.append(grp)
            beConObj = parGrp[0]
            grp_data = {cur:parGrp}
        resultData.update(grp_data)

        cmds.delete(cmds.parentConstraint(fk_lst[i], beConObj))
        cmds.parent(beConObj, fk_lst[i])
        child = data[fk_lst[i]]
        if not child:
            continue
        cmds.parent(child, cur)
    return [curLst,resultData]

def averageCons(startCon, endCon, beConLst, andOne=False):
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
        con_node = cmds.parentConstraint(startCon, endCon, beConLst[i], mo=True)[0]
        cmds.setAttr("{}.{}W0".format(con_node, startCon), first_value)
        cmds.setAttr("{}.{}W1".format(con_node, endCon), next_value)
        parConLst.append(con_node)
    return parConLst
