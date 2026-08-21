import pymel.core as pm
from contextlib import contextmanager

def createGrp():
    pm.select(cl=True)
    if pm.objExists('RIG_Other'):
        pass
    else:
        Deformation_Attrs = ['t','r','s']
        RIG_Other = pm.group(n='RIG_Other')
        for Deformation_Attr in Deformation_Attrs:
            pm.setAttr('{}.{}'.format(RIG_Other,Deformation_Attr),lock=True)

def lockAndHideAttrs(ctl,attrs):
    for attr in attrs:
        if ctl.hasAttr(attr):
            attr = ctl.attr(attr)
            attr.setLocked(True)
            attr.setKeyable(False)
            attr.showInChannelBox(False)
            
@contextmanager
def createControl(src_shape,dst):
    curve = pm.createNode('nurbsCurve')
    src_shape.ws[0] >> curve.cr
    yield curve
    
    shape = dst.getShape()
    if not shape:
        pm.parent(curve,dst,add=True,shape=True)
    else:
        curve.ws[0] >> shape.cr
    pm.disconnectAttr(src_shape.ws[0],curve.cr)
    pm.refresh()
    pm.delete(curve.getParent())
    
def adjustShapeStyle_ladder(curve):
    pm.select(curve.cv)
    pm.scale([.8,4,.8],r=True,ocp=True)
    pm.select(curve.cv[0],curve.cv[5:10],curve.cv[15])
    pm.scale([.6,1,.6],r=True,ocp=True)
    pm.select(curve)
    
def adjustShapeStyle_scale(curve):
    pm.select(curve.cv)
    pm.scale([.7,1,.7],r=True,ocp=True)
    
def replace_parentConstraint(ikSpline,ik_fixGrp,follow):
    parentNode = ikSpline.getAllParents()[1]
    pcnode = pm.parentConstraint(ik_fixGrp,follow,parentNode,mo=True)
    uds = pcnode.listAttr(ud=True)
    unitCv = ikSpline.followEnd.outputs()[0]
    reverse = unitCv.output.outputs()[0]
    reverse.ox >> uds[0]
    unitCv.o >> uds[1]
    
def connect_shape(name1,name2):
    #name1,name2 = 'IKExtraSpine1_M','IKSpine1_M'
    
    node1s = pm.ls(name1)
    node2s = pm.ls(name2)
    
    if not len(node1s) or not len(node2s):
        return
    
    node1, node2 = node1s[0],node2s[0]
    shape = node1.getShape()
    # rename ...
    shape_name = '{}Shape'.format(node1)
    if str(shape) != shape_name:
        shape.rename(shape_name)
        
    node2_shape = node2.getShape()
    if node2_shape:
        node2_shape.v >> shape.v

def add_SplineIKConVis_attr():
    attr_name = 'SplineIKConVis'
    nodes = pm.ls('FKIKSpine_M')
    
    if len(nodes) != 1:
        return
    
    node = nodes[0]
    
    if not node.hasAttr(attr_name):
        node.addAttr(attr_name,at='bool')
        
    node_attr = node.attr(attr_name)
    node_attr.setKeyable(False)
    node_attr.showInChannelBox(True)
    
    iksp_names = ['IKSpine2_M','IKSpine3_M','IKSpine4_M']
    
    for iksp_name in iksp_names:
        iksp_nodes = pm.ls(iksp_name)
        if len(iksp_nodes) == 1:
            try:
                iksp_attr = iksp_nodes[0].v
                node_attr >> iksp_attr
                iksp_attr.setKeyable(False)
                iksp_attr.showInChannelBox(False)
            except:
                pass

def fix_adv_spine():
    fix_grp = 'IKSpineFix_Grp'
    
    ikhySpines = pm.ls('IKhybridSpine*_M')
    if not len(ikhySpines):
        pm.warning('Scene not find (ADV) rig.')
        return
    
    if pm.objExists(fix_grp):
        pm.warning('(ADV) fix node exists!')
        return
        
    node = pm.createNode('transform',name=fix_grp)
    node.v.set(0)
    [attr.setLocked(True) for attr in node.listAttr(k=True)]
    
    # RIG_Other
    if pm.objExists('RIG_Other'):
        pm.parent(node,'RIG_Other')
    
    ikSplines = pm.ls(regex='IKSpine\d*_M')
    ikSplines.sort()
    
    ikSpineCurve = pm.PyNode('IKSpineCurve_M')
    ikSpineCurveShape = ikSpineCurve.getShape()
    
    # disconnect locater controls
    for cv, _ in ikSpineCurveShape.controlPoints.inputs(c=True,p=True):
        cv.disconnect()
        
    ikSpineCurve_fix = 'IKSpineCurve_M_Fix'
    ikSpineCurve_fix = pm.duplicate(ikSpineCurve, rr=True,name=ikSpineCurve_fix)[0]
    
    pm.parent(ikSpineCurve_fix,fix_grp)
    rebuildCurve_mel = 'rebuildCurve -ch 1 -rpo 1 -rt 0 -end 1 -kr 0 -kcp 0 -kep 1 -kt 0 -s 4 -d 3 -tol 0.01 "{}";'
    pm.mel.eval(rebuildCurve_mel.format(ikSpineCurve_fix))
    
    pm.refresh()
    
    # create new curve skin joints
    sp_fix_jnts = []
    for i, ikhySpine in enumerate(ikhySpines):
        jnt = pm.createNode('joint',name='Spline_Fix_{}'.format(i+1))
        pm.delete(pm.pointConstraint(ikhySpine, jnt))
        sp_fix_jnts.append(jnt)
        
    for ikSpline, sp_fix_jnt in zip(ikSplines, sp_fix_jnts):
        pm.parentConstraint(ikSpline, sp_fix_jnt , mo=True)
        pm.scaleConstraint(ikSpline, sp_fix_jnt , mo=True)
        
    pm.parent(sp_fix_jnts, fix_grp)
    
    pm.select(sp_fix_jnts,ikSpineCurve_fix)
    pm.mel.eval('newSkinCluster "-toSelectedBones -bindMethod 0 -normalizeWeights 1 -weightDistribution 0 -mi 3 -dr 4 -rui  false,multipleBindPose,1";')
    
    ik_fixGrps = []
    for ikSpline in ikSplines[1:-1]:
        node =pm.createNode('transform', name='{}_FixGrp'.format(ikSpline))
        pm.delete(pm.pointConstraint(ikSpline,node))
        ik_fixGrps.append(node)
        
    pm.parent(ik_fixGrps,fix_grp)
    
    for ikhy, ik_fixGrp in zip(ikhySpines[1:-1], ik_fixGrps):
        pm.parentConstraint(ikhy, ik_fixGrp, mo=True)
        
    old_pc_nodes = []
    for ikSpline in ikSplines[1:-1]:
        parentNode = ikSpline.getAllParents()[1]
        old_pc_nodes.append(parentNode.getChildren(type='parentConstraint')[0])
        
    pm.delete(old_pc_nodes)
    
    follows = pm.ls(regex='IKFollowEndSpine\d+_M')
    
    replace_parentConstraint(ikSplines[1],ik_fixGrps[0],follows[0])
    pm.parentConstraint(ik_fixGrps[1],ikSplines[2].getAllParents()[1], mo=True)
    replace_parentConstraint(ikSplines[3],ik_fixGrps[2],follows[-1])

    ikSplines[1].followEnd.set(4)
    ikSplines[3].followEnd.set(6)

    root_ctl = ikSplines[0]
    root_shape = root_ctl.getShape()
    root_parent = root_ctl.getParent()
    # Set Pivot
    Spine1_M = pm.PyNode('Spine1_M')
    spivot = Spine1_M.getScalePivot(space='world')
    root_parent.setScalePivot(spivot, space='world')
    root_parent.setRotatePivot(spivot, space='world')
    
    with createControl(root_shape, root_parent) as tmpCurve:
        adjustShapeStyle_ladder(tmpCurve)
        tmpCurve.ove.set(1)
        tmpCurve.ovc.set(17)
        
    for ikSpline in ikSplines[1:-1]:
        with createControl(root_shape, ikSpline) as tmpCurve:
            adjustShapeStyle_scale(tmpCurve)
            
    for ikhySpine in ikhySpines:
        shape = ikhySpine.getShape()
        if shape:
            shape.ovc.set(18)
    # hide attribute
    attrs = ['ikCvVis','ikHybridVis','stiff','follow']
    lockAndHideAttrs(ikSplines[-1],attrs)
    
    for x in [ikhySpines[0], ikhySpines[-1]]:
        s = x.getShape()
        if s:
            s.lodv.set(0)
    
    connect_shape(root_parent, root_ctl)
    
    add_SplineIKConVis_attr()


def ZningAddFix():
    WireNode = pm.mel.eval('wire -gw false -en 1.000000 -ce 0.000000 -li 0.000000 -w IKSpineCurve_M_Fix IKSpineCurve_M;')
    WireNode = pm.PyNode(WireNode[0])
    WireNode.dropoffDistance[0].set(100)
    
    FKIKSpineNode = 'FKIKSpine_M'
    FKIKSpineNode = pm.PyNode(FKIKSpineNode)
    FKIKSpineNode.SplineIKConVis.set(1)
    FKIKSpineNode.FKIKBlend.set(10)
    
    MainName1,MainName2,MainName3,MainName4,MainName5,MainName6 = 'FitSkeleton','MotionSystem','DeformationSystem','Main','MainExtra2','MainExtra1'
    MainName4Node = pm.PyNode(MainName4)
    MainName5Node = pm.PyNode(MainName5)
    MainName6Node = pm.PyNode(MainName6)
    MainName4Node.rename('MainExtra2')
    MainName5Node.rename('Main')
    MainName4Node.v.set(lock=True,keyable=False,channelBox=False)
    MainName5Node.v.set(lock=True,keyable=False,channelBox=False)
    MainName6Node.v.set(lock=True,keyable=False,channelBox=False)
    pm.addAttr(MainName5Node,ln='height',k=False, at='double')
    pm.addAttr(MainName5Node,ln='version',k=False, at='double')
    MainName4Node.height >> MainName5Node.height
    MainName4Node.version >> MainName5Node.version
    pm.setAttr(MainName5Node.height,lock=True,keyable=False,channelBox=False)
    pm.setAttr(MainName5Node.version,lock=True,keyable=False,channelBox=False)

    pm.connectAttr(FKIKSpineNode.SplineIKConVis,'IKSpine1_M.v')
    pm.connectAttr(FKIKSpineNode.SplineIKConVis,'IKSpine5_M.v')
    pm.setAttr('IKSpine5_M.v', keyable=False, channelBox=False)
    pm.setAttr('IKSpine1_M.v', keyable=False, channelBox=False)

    MainName5Node.addAttr('globalScale',k=True, at='double', dv=1)
    MainName5Node.globalScale >> MainName5Node.sx
    MainName5Node.globalScale >> MainName5Node.sy
    MainName5Node.globalScale >> MainName5Node.sz
    pm.matchTransform('HipSwingerOffset_M', 'Spine1_M', pos=True)

    pm.setAttr('FKOffsetJaw_M.v', 0)
    pm.setAttr('FKOffsetJaw_M.v', lock=True)

    MainName4Node.getShape().lineWidth.set(2)
    MainName5Node.getShape().lineWidth.set(2)
    MainName6Node.getShape().lineWidth.set(2)
    pm.setAttr('RootX_MShape.lineWidth', 2)
    pm.setAttr('IKSpine3_M.followEnd',lock=True,keyable=False, channelBox=False)
    pm.setAttr('IKSpine1_M.stiff',lock=True,keyable=False, channelBox=False)
    
    Attrs = ['sx','sy','sz']
    for Attr in Attrs:
        pm.setAttr('{}.{}'.format(MainName5Node,Attr),lock=True,keyable=False,channelBox=False)
        pm.setAttr('{}.{}'.format(MainName6Node,Attr),lock=True,keyable=False,channelBox=False)
        pm.setAttr('{}.{}'.format(MainName4Node,Attr),lock=True,keyable=False,channelBox=False)
    
    for i in ['_L','_R']:
        if pm.objExists('IKLeg{}.legAim'.format(i)):
            pm.setAttr('IKLeg{}.legAim'.format(i),0)
    
    if not pm.objExists('Group'):
        pm.error('Please Create ADV frist !')
    else:
        pm.parent('RIG_Other','Group')
        
    pm.select(cl=True)
    pm.inViewMessage(amg='Fix ADV Spine: <hl>Fianl</hl>',pos='midCenterTop',fade=False,dk=True)

def createGlobalSpace():
    try:
        import create_globalSpace
    except ImportError:
        pm.warning('No module: create_globalSpace, skip create global space')
        return
    ctrlNames = ['FKShoulder_L','FKShoulder_R','FKHead_M']
    for ctrlName in ctrlNames:
        create_globalSpace.createGlobalSpace(pm.PyNode(ctrlName))

def run():
    createGrp()   
    fix_adv_spine() 
    ZningAddFix() 
    createGlobalSpace()

if __name__ == "__main__":
    run()