import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya

def create_node(nodeType,name):
    if not cmds.objExists(name):
        node = cmds.createNode(nodeType,n=name)
    else:
        node = name
    return node

def connect_attr(source,target,source_i=['X','Y','Z'],target_i=['X','Y','Z']):
    for a, b in list(zip(source_i,target_i)):
        cmds.connectAttr(source+a, target+b, f=True)

def matrix_constrain(drivers, drivens):
    for driver, driven in list(zip(drivers,drivens)):
        multMatrix = create_node("multMatrix",'{}_MatrixConstrain_multMatrix'.format(driven))
        decomposeMatrix = create_node("decomposeMatrix",'{}_MatrixConstrain_decomposeMatrix'.format(driven))
        offset = (  
            OpenMaya.MMatrix(cmds.getAttr("{}.worldMatrix[0]".format(driven)))
            #* OpenMaya.MMatrix(cmds.getAttr("{}.matrix".format(driven))).inverse()
            * OpenMaya.MMatrix(cmds.getAttr("{}.worldInverseMatrix[0]".format(driver)))
        )
        cmds.setAttr("{}.matrixIn[0]".format(multMatrix), offset, type="matrix")
        cmds.connectAttr("{}.worldMatrix[0]".format(driver), "{}.matrixIn[1]".format(multMatrix),f=True)
        cmds.connectAttr("{}.parentInverseMatrix[0]".format(driven), "{}.matrixIn[2]".format(multMatrix),f=True)
        
        cmds.connectAttr("{}.matrixSum".format(multMatrix), "{}.inputMatrix".format(decomposeMatrix),f=True)
        connect_attr("{}.outputTranslate".format(decomposeMatrix), "{}.translate".format(driven))
        connect_attr("{}.outputRotate".format(decomposeMatrix), "{}.rotate".format(driven))
        connect_attr("{}.outputScale".format(decomposeMatrix), "{}.scale".format(driven))
        connect_attr("{}.outputShear".format(decomposeMatrix), "{}.shear".format(driven),target_i=['XY','XZ','YZ'])
        
        #cmds.connectAttr("{}.matrixSum".format(multMatrix), "{}.offsetParentMatrix".format(driven),f=True)

        cmds.connectAttr('{}.{}'.format(driven,'rotateOrder'), '{}.{}'.format(decomposeMatrix,'inputRotateOrder'),f=True)

drivers = cmds.ls(sl=True)
drivens = cmds.ls(sl=True)
matrix_constrain(drivers, drivens)