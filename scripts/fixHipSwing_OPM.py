import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya

orig_t = cmds.getAttr('HipSwingReverse.t')
io_MD = cmds.createNode('multiplyDivide',n='fixHipSwing_t_MD')
cmds.setAttr('{}.input2'.format(io_MD),-1,-1,-1)
cmds.connectAttr("HipSwingReverse.t", "{}.input1".format(io_MD),f=True)
cmds.connectAttr("{}.output".format(io_MD), "HipSwingReverseRoot.t",f=True)
cmds.matchTransform('HipSwingReverse','FKXSpine1Part1_M',pos=True,rot=False,scl=False,piv=False)
cmds.connectAttr("HipSwingReverse.t", "HipSwingerOffset_M.t",f=True)
fixed_t = cmds.getAttr('HipSwingReverse.t')

cmds.spaceLocator(n='fixHipSwing_jnt_LOC')
cmds.spaceLocator(n='fixHipSwing_grp_LOC')

cmds.parent('fixHipSwing_jnt_LOC','FKXRoot_M')
cmds.matchTransform('fixHipSwing_jnt_LOC','FKXSpine1_M')
cmds.parent('fixHipSwing_grp_LOC','FKOffsetSpine1_M')
cmds.matchTransform('fixHipSwing_grp_LOC','FKXSpine1_M')
cmds.setAttr('fixHipSwing_jnt_LOCShape.v',0)
cmds.setAttr('fixHipSwing_grp_LOCShape.v',0)


io_BM = 'fixHipSwing_BM'
io_UC = 'fixHipSwing_UnitConversion'
io_attr = 'fix'
const_MM = 'fixHipSwing_MM'
node = 'FKXSpine1_M'
driver = 'fixHipSwing_jnt_LOC'
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

cmds.connectAttr("{}.worldInverseMatrix[0]".format('FKOffsetSpine1_M'), "{}.matrixIn[2]".format(mult),f=True)
cmds.connectAttr("{}.matrixSum".format('Spine1InbetweenMM_M'), "{}.matrixIn[3]".format(mult),f=True)
cmds.connectAttr("{}.matrixSum".format('Spine1InbetweenMM_M'), "{}.offsetParentMatrix".format('fixHipSwing_grp_LOC'),f=True)
cmds.connectAttr("{}.worldMatrix[0]".format('fixHipSwing_grp_LOC'), "{}.matrixIn[1]".format('Spine1Part1NoShearMM_M'),f=True)

cmds.createNode('blendMatrix',n=io_BM)
#cmds.connectAttr("{}.matrixSum".format(mult), "{}.offsetParentMatrix".format(node),f=True)
cmds.connectAttr("{}.matrixSum".format('Spine1InbetweenMM_M'), "{}.inputMatrix".format(io_BM),f=True)
cmds.connectAttr("{}.matrixSum".format(mult), "{}.target[0].targetMatrix".format(io_BM),f=True)
cmds.connectAttr("{}.outputMatrix".format(io_BM), "{}.offsetParentMatrix".format(node),f=True)

cmds.addAttr('HipSwinger_M', ln=io_attr, at='double', min=0, max=10, dv=0, k=True)
cmds.createNode('unitConversion',n=io_UC)
cmds.setAttr('{}.conversionFactor'.format(io_UC),0.1)
cmds.connectAttr("HipSwinger_M.fix", "{}.input".format(io_UC),f=True)
cmds.connectAttr("{}.output".format(io_UC), "{}.target[0].weight".format(io_BM),f=True)
for axis, idx in zip(['X', 'Y', 'Z'], [0, 1, 2]):
    # 当 =0 时
    cmds.setDrivenKeyframe(
        "HipSwingReverse.translate{}".format(axis),
        cd="HipSwinger_M.{}".format(io_attr),
        driverValue=0,
        value=orig_t[0][idx]
    )
    
    # 当 =10 时
    cmds.setDrivenKeyframe(
        "HipSwingReverse.translate{}".format(axis),
        cd="HipSwinger_M.{}".format(io_attr),
        driverValue=10,
        value=fixed_t[0][idx]
    )
