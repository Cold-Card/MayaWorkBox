import pymel.core as pm
jnts = pm.ls(sl=True)
for jnt in jnts:
    pm.PyNode(jnt)
    jntName = '_'.join(jnt.split('_')[:-1])
    side = jnt.split('_')[-1]
    mm = pm.PyNode(jntName+'MM_'+side)
    source_decompose = pm.PyNode(jnt+'_source_decompose')
    rotation_decompose = pm.PyNode(jnt+'_rotation_decompose')
    mm.matrixSum >> jnt.offsetParentMatrix
    for u,i,o,p in list(zip(['x','y','z'],['X','Y','Z'],['XY','XZ','YZ'],['R','G','B'])):
        pm.disconnectAttr(source_decompose+'.outputTranslate'+i, jnt+'.t'+u)
        pm.disconnectAttr(source_decompose+'.outputShear'+i, jnt+'.shear'+o)
        pm.disconnectAttr(rotation_decompose+'.outputRotate'+i, jnt+'.r'+u)
        pm.setAttr(jnt+'.t'+u,0)
        pm.setAttr(jnt+'.r'+u,0)
        if pm.objExists(jnt+'_scale_mult'):
            scaleBlend = pm.PyNode(pm.listConnections(jnt+'_scale_mult.input1X',d=False,p=False,t='blendColors')[0])
            pm.connectAttr(scaleBlend+'.output'+p, jnt+'.s'+u,f=True)
        else:
            pm.disconnectAttr(source_decompose+'.outputScale'+i, jnt+'.s'+u)
            pm.setAttr(jnt+'.s'+u,1)
    jnt.jointOrient.set(0,0,0)