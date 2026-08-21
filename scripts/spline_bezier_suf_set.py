import pymel.core as pm

sufs = pm.ls(sl=True)
for suf in sufs:
    suf_bezier = pm.duplicate(suf,n='{}_bezier'.format(suf))[0]
    
    u_spans = suf.spansU.get()
    pm.rebuildSurface(suf,ch=1,rpo=1,rt=0,kr=0,su=u_spans*10,du=3,sv=0,dv=1)
    pm.rebuildSurface(suf_bezier,ch=1,rpo=1,rt=7,kr=0,su=0,du=3,sv=0,dv=1)
    
    pm.select(suf,suf_bezier,r=True)
    pm.mel.eval('CreateWrap;')
    '''
    crv_00 = pm.createNode('nurbsCurve').getParent().rename('{}_crv_00'.format(suf_bezier))
    crv_01 = pm.createNode('nurbsCurve').getParent().rename('{}_crv_01'.format(suf_bezier))
    CFS_00 = pm.createNode('curveFromSurfaceIso',n='{}_CFS'.format(crv_00))
    CFS_01 = pm.createNode('curveFromSurfaceIso',n='{}_CFS'.format(crv_01)) 
    CFS_00.isoparmValue.set(0)
    CFS_01.isoparmValue.set(1)
    suf_bezier.worldSpace[0] >> CFS_00.inputSurface
    suf_bezier.worldSpace[0] >> CFS_01.inputSurface
    CFS_00.outputCurve >> crv_00.create
    CFS_01.outputCurve >> crv_01.create
    
    wireNode = pm.wire(suf,w=[crv_00,crv_01])[0]
    wireNode.dropoffDistance[0].set(0.1)
    wireNode.dropoffDistance[1].set(0.1)
    '''