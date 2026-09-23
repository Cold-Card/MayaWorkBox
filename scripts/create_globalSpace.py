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
    
def addAttr(nodeName,attrName,minValue=None, maxValue=None, keyable=True, attributeType="float", defaultValue=0,enumName=None): 
    if pm.objExists(nodeName):
        nodeName = pm.PyNode(nodeName)
        if not nodeName.hasAttr(attrName):
            if enumName is not None:
                pm.addAttr(nodeName,longName=attrName, enumName=enumName, keyable=keyable, attributeType=attributeType, defaultValue=defaultValue)
            elif minValue is not None and maxValue is not None:
                pm.addAttr(nodeName,longName=attrName, minValue=minValue, maxValue=maxValue, keyable=keyable, attributeType=attributeType, defaultValue=defaultValue)
            elif minValue is not None:
                pm.addAttr(nodeName,longName=attrName, minValue=minValue, keyable=keyable, attributeType=attributeType, defaultValue=defaultValue)
            elif maxValue is not None:
                pm.addAttr(nodeName,longName=attrName, maxValue=maxValue, keyable=keyable, attributeType=attributeType, defaultValue=defaultValue)
            else:
                pm.addAttr(nodeName,longName=attrName, keyable=keyable, attributeType=attributeType, defaultValue=defaultValue)
            if not keyable:
                pm.setAttr(f'{nodeName}.{attrName}', e=True, channelBox=True)
        return nodeName.attr(attrName)
    else:
        print('{} 不存在'.format(nodeName))
    
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


def createGlobalSpace(spaceObj_list_data,drivenObj_list,drivenGroup_list,ctrl_list):
    for index, drivenObj in enumerate(drivenObj_list):
        drivenBM = createNode('blendMatrix',drivenObj + '_globalSpace_BM')
        ioBM = createNode('blendMatrix',drivenObj + '_globalSpace_io_BM')
        drivenMM = createNode('multMatrix',drivenObj + '_globalSpace_MM')
        drivenPM = createNode('pickMatrix',drivenObj + '_globalSpace_PM',{'useTranslate':0,'useRotate':1,'useScale':0,'useShear':0})
        drivenObj_mat = pm.xform(drivenObj, q=True, ws=True, matrix=True)
        drivenMM.matrixIn[0].set(drivenObj_mat)
        drivenBM.outputMatrix >> drivenMM.matrixIn[1]
        #if not pm.objExists(drivenObj + '_globalSpace_grp'):
        #    drivenGroup = pm.group(drivenObj, n=drivenObj + '_globalSpace_grp')
        #drivenGroup = pm.PyNode(drivenObj + '_globalSpace_grp')
        drivenGroup = pm.PyNode(drivenGroup_list[index])
        drivenGroup.worldInverseMatrix[0] >> drivenMM.matrixIn[2]
        drivenMM.matrixSum >> drivenPM.inputMatrix

        for i, space in enumerate(list(spaceObj_list_data.keys())):
            spaceObj = pm.PyNode(list(spaceObj_list_data.items())[i][1])
            spaceMM = createNode('multMatrix',spaceObj + '_globalSpace_MM')
            rel_mat = om2.MMatrix(pm.xform(spaceObj, q=True, ws=True, matrix=True)).inverse()
            spaceMM.matrixIn[0].set(rel_mat)
            spaceObj.worldMatrix[0] >> spaceMM.matrixIn[1]
            spaceMM.matrixSum >> drivenBM.target[i].targetMatrix
            
            #drivenValues = [0,0,0]
            #drivenValues[i] = 1
            #print(drivenValues)
            #setSDK([globalSpaceAttr],[spaceBM.target[i].weight],[timeLists],[drivenValues])

        spaceAttr = addAttr(ctrl_list[index],space,minValue=0, maxValue=1)
        spaceAttr >> ioBM.target[0].weight
        drivenPM.outputMatrix >> ioBM.target[0].targetMatrix
        ioBM.outputMatrix >> drivenObj.offsetParentMatrix


if __name__ == '__main__':
    createNode('transform','pathArea_global_loc')
    spaceObj_list_data = {
    'global':'pathArea_global_loc'
    }
    drivenObj_list = pm.ls(sl=True)
    drivenGroup_list = pm.ls(sl=True)
    ctrl_list = pm.ls(sl=True)
    createGlobalSpace(spaceObj_list_data,drivenObj_list,drivenGroup_list,ctrl_list)
    
 