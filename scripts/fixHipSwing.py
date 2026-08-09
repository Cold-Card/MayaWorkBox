import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya

cmds.matchTransform('HipSwingerOffset_M','FKXSpine1Part1_M',pos=True,rot=False,scl=False,piv=False)
cmds.parent('HipSwingReverseRoot',w=True)
cmds.matchTransform('HipSwingReverse','FKXSpine1Part1_M',pos=True,rot=False,scl=False,piv=False)
cmds.parent('HipSwingReverseRoot','HipSwingReverse')
cmds.delete('FKOffsetSpine1_M_pointConstraint1')
cmds.group(em=True,n='FKOffsetSpine1_M_fixHipSwing_offset_Grp',p='FKOffsetSpine1_M')
cmds.parent(
        'FKExtraSpine1_M',
        'FKXSpine1_M',
        'InbetweenBaseSpine1_M',
        'InbetweenSpine1_M',
        'InbetweenSpine1Part1_M',
        'FKOffsetSpine1_M_fixHipSwing_offset_Grp'
    )
cmds.parent('FKOffsetSpine1_M_fixHipSwing_offset_Grp',w=True)
cmds.matchTransform('FKOffsetSpine1_M','FKXSpine1Part1_M',pos=True,rot=False,scl=False,piv=False)
cmds.parent('FKOffsetSpine1_M_fixHipSwing_offset_Grp','FKOffsetSpine1_M')
cmds.pointConstraint('FKPS2Spine1_M','FKOffsetSpine1_M',mo=True)
cmds.group(em=True,n='FKXSpine1_M_fixHipSwing_offset_Grp',p='FKXSpine1_M')
cmds.parent('FKOffsetSpine1Part1_M','FKPS1Spine1Part1_M','FKXSpine1_M_fixHipSwing_offset_Grp')
cmds.parent('FKXSpine1_M_fixHipSwing_offset_Grp','FKOffsetSpine1_M_fixHipSwing_offset_Grp')


const_MM = 'fixHipSwing_MM_01'
jnt_MM = 'fixHipSwing_MM_02'
grp_DM = 'fixHipSwing_DM'
node = 'FKXSpine1_M_fixHipSwing_offset_Grp'
driver = 'FKPS2Spine1_M'
mult = cmds.createNode("multMatrix",n=const_MM)
offset = (  
    OpenMaya.MMatrix(cmds.getAttr("{}.worldMatrix[0]".format(node)))
    * OpenMaya.MMatrix(cmds.getAttr("{}.matrix".format(node))).inverse()
    * OpenMaya.MMatrix(cmds.getAttr("{}.worldInverseMatrix[0]".format(driver)))
)
cmds.setAttr("{}.matrixIn[0]".format(mult), offset, type="matrix")

cmds.connectAttr("{}.worldMatrix[0]".format(driver), "{}.matrixIn[1]".format(mult))

'''parent = cmds.listRelatives(node, parent=True, path=True)
if parent:
    cmds.connectAttr("{}.worldInverseMatrix[0]".format(parent[0]), "{}.matrixIn[2]".format(mult))'''

cmds.connectAttr("{}.worldInverseMatrix[0]".format('FKOffsetSpine1_M_fixHipSwing_offset_Grp'), "{}.matrixIn[2]".format(mult))

cmds.createNode("multMatrix",n=jnt_MM)
cmds.createNode("decomposeMatrix",n=grp_DM)
cmds.connectAttr("{}.matrixSum".format(mult), "{}.matrixIn[0]".format(jnt_MM),f=True)
cmds.connectAttr("{}.matrixSum".format('Spine1InbetweenMM_M'), "{}.matrixIn[1]".format(jnt_MM),f=True)
cmds.connectAttr("{}.matrixSum".format(jnt_MM), "{}.inputMatrix".format('FKXSpine1DM_M'),f=True)

cmds.connectAttr("{}.matrixSum".format('Spine1InbetweenMM_M'), "{}.inputMatrix".format(grp_DM),f=True)
cmds.connectAttr('{}.outputRotate'.format(grp_DM),'{}.rotate'.format(node),f=True)
cmds.connectAttr('{}.outputScale'.format(grp_DM),'{}.scale'.format(node),f=True)
cmds.connectAttr('{}.outputShear'.format(grp_DM),'{}.shear'.format(node),f=True)
cmds.connectAttr('{}.outputTranslate'.format(grp_DM),'{}.translate'.format(node),f=True)