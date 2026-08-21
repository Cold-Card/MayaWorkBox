import pymel.core as pm

objs = pm.ls(sl=True)

for obj in objs:
    
    POS = obj.t.inputs()[0]
    #POS = pm.createNode('pointOnSurfaceInfo',n=base_name+'_POS_'+str(i))
    FBFM = pm.createNode('fourByFourMatrix',n=obj+'_FBFM')
    decomposeMatrix = pm.createNode('decomposeMatrix',n=obj+'_decomposeMatrix')
    
    for x,y in enumerate(['X','Y','Z']):
        print(x,y)
        pm.connectAttr('{}.{}'.format(POS,'position'+y),'{}.{}'.format(FBFM,'in3'+str(x)))
        pm.connectAttr('{}.{}'.format(POS,'normal'+y),'{}.{}'.format(FBFM,'in0'+str(x)))

    for x,y in enumerate(['x','y','z']):
        pm.connectAttr('{}.{}'.format(POS,'tangentU'+y),'{}.{}'.format(FBFM,'in1'+str(x)))
        pm.connectAttr('{}.{}'.format(POS,'tangentV'+y),'{}.{}'.format(FBFM,'in2'+str(x)))
    
    FBFM.output >> decomposeMatrix.inputMatrix
    decomposeMatrix.outputTranslate >> obj.t
    decomposeMatrix.outputRotate >> obj.r