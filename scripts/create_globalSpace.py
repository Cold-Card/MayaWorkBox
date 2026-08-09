import pymel.core as pm
import maya.cmds as cmds
import maya.api.OpenMaya as om2

def createNode(nodeType,nodeName,editData={}):
    if not pm.objExists(nodeName):
        pm.createNode(nodeType,n=nodeName)
    nodeName = pm.PyNode(nodeName)
    for attrName, value in editData.items():
        if nodeName.hasAttr(attrName):
            try:
                nodeName.attr(attrName).set(value)
            except:
                continue
        else:
            print('{} 没有属性：{}'.format(nodeName,attrName))
    return nodeName
    
def addAttr(nodeName,attrName,spaces=[]): 
    if not nodeName.hasAttr(attrName):
        enum=':'.join(spaces)
        nodeName.addAttr(attrName,at='enum',enumName=enum,k=True)
    return nodeName.attr(attrName)
    
def get_relative_matrix(objA, objB):
    """
    计算 objA 在 objB 坐标系下的变换矩阵（行主序 4x4）
    返回 om2.MMatrix 对象，可直接用于点转换
    """
    # 获取世界矩阵（16个浮点数，行主序）
    matA_list = pm.xform(objA, q=True, ws=True, matrix=True)
    matB_list = pm.xform(objB, q=True, ws=True, matrix=True)

    # 转换为 MMatrix
    matA = om2.MMatrix(matA_list)
    matB = om2.MMatrix(matB_list)

    # 计算相对矩阵：M_rel = M_A * inv(M_B)
    matB_inv = matB.inverse()
    rel_mat = matA * matB_inv
    return rel_mat

def setSDK(drivers,drivens,timeLists,drivenValues):
    '''drivers = ['FKShoulder_R.globalSpace']
    drivens = ['blendMatrix1.target[0].weight','blendMatrix1.target[1].weight','blendMatrix1.target[2].weight']
    timeLists = [[0,1,2]]
    drivenValues = [[1,0,0],[0,1,0],[0,0,1]]'''
    if len(drivenValues) == 1:
        drivenValues = [drivenValues[0]]*len(drivens)
    for i, (driven, drivenValue) in enumerate(list(zip(drivens,drivenValues))):
        if len(timeLists) == 1:
            timeList = timeLists[0]
        else:
            timeList = timeLists[i]
        for idx, time in enumerate(timeList):
            cmds.setDrivenKeyframe(
                f"{driven}",
                cd=f"{drivers[0]}",
                driverValue=time,
                value=drivenValue[idx]
            )

spaceData = {
    'Main':'MainExtra2',
    'Root':'RootX_M',
    'Chest':'Chest_M'
}

def createGlobalSpace(ctrlName,spaces=spaceData):
    if not spaces:
        pm.warning('No Space')
        return
    partsName = ctrlName.split('_')[0][2:]
    #print(partsName)
    side = '_' + ctrlName.split('_')[1]
    fkGlobalGrp = 'FKGlobal' + partsName + side
    if not pm.objExists(fkGlobalGrp):
        pm.warning('No Global Grp')
        return
    globalSpaceAttr = addAttr(ctrlName,'globalSpace',list(spaces.keys()))
    fkGlobalMM = pm.PyNode('FKGlobal' + partsName + 'MM' + side)
    spaceBM = createNode('blendMatrix','FKGlobalSpace' + partsName + 'BM' + side)
    timeLists = []
    for a in range(0,len(list(spaces.items()))):
        timeLists.append(a)
    #print(timeLists)
    for i, space in enumerate(list(spaces.keys())):
        followObj = pm.PyNode(list(spaces.items())[i][1])
        #print(followObj)
        spaceMM = createNode('multMatrix','FKGlobalSpace' + space + partsName + 'MM' + side)
        rel_mat = get_relative_matrix('Main',followObj)
        spaceMM.matrixIn[0].set(rel_mat)
        followObj.worldMatrix[0] >> spaceMM.matrixIn[1]
        spaceMM.matrixSum >> spaceBM.target[i].targetMatrix
        drivenValues = [0,0,0]
        drivenValues[i] = 1
        #print(drivenValues)
        setSDK([globalSpaceAttr],[spaceBM.target[i].weight],[timeLists],[drivenValues])
    spaceBM.outputMatrix >> fkGlobalMM.matrixIn[1]

if __name__ == '__main__':
    ctrlNames = pm.ls(sl=True)
    for ctrlName in ctrlNames:
        createGlobalSpace(ctrlName)
    
 