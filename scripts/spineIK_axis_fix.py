import pymel.core as pm
import maya.cmds as cmds
import maya.api.OpenMaya as om2

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
    '''
    with createControl(root_shape, root_parent) as tmpCurve:
        adjustShapeStyle_ladder(tmpCurve)
        tmpCurve.ove.set(1)
        tmpCurve.ovc.set(17)
    
    for ikSpline in ikSplines[1:-1]:
        with createControl(root_shape, ikSpline) as tmpCurve:
            adjustShapeStyle_scale(tmpCurve)
    '''       
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

    pm.select(cl=True)
    pm.inViewMessage(amg='Fix ADV Spine: <hl>Fianl</hl>',pos='midCenterTop',fade=False,dk=True)

def run():
    createGrp()   
    fix_adv_spine() 
    ZningAddFix() 

zeroIK = {
    'IKhybridSpine5_M': [['IKOffsetSpine5_M', 'IKSpine5LocalOrient0_M', 'IKSpine5LocalOrient1_M'], ['IKSpine5LocalStartOrient_M']],
    'IKhybridSpine1_M': [['IKOffsetSpine1_M', 'IKSpine1LocalOrient0_M'], ['IKSpine1LocalOrient1_M']],
    'IKhybridSpine2_M': [['IKOffsetSpine2_M'], ['IKSpine2LocalOrient1_M']],
    'IKhybridSpine3_M': [['IKOffsetSpine3_M'], ['IKSpine3LocalOrient1_M']],
    'IKhybridSpine4_M': [['IKOffsetSpine4_M'], ['IKSpine4LocalOrient1_M']]
}

def get_relative_matrix(objA, objB):
    """
    计算 objA 在 objB 坐标系下的变换矩阵（行主序 4x4）
    返回 om2.MMatrix 对象，可直接用于点转换
    """
    # 转换为 MMatrix
    matA = om2.MMatrix(objA)
    matB = om2.MMatrix(objB)

    # 计算相对矩阵：M_rel = M_A * inv(M_B)
    matB_inv = matB.inverse()
    rel_mat = matA * matB_inv
    return rel_mat

def ikCtrl_shape_fix(ikCtrl):
    curve = pm.createNode('nurbsCurve')
    ikCtrl.ws[0] >> curve.cr
    ikCtrl.ws[0] // curve.cr
    rel_matrix = get_relative_matrix(pm.xform(curve.getParent(), q=True, ws=True, matrix=True), pm.xform(ikCtrl, q=True, ws=True, matrix=True))
    pm.xform(curve.getParent(), ws=True, matrix=list(rel_matrix))
    pm.makeIdentity( curve.getParent(), apply=True, t=False,r=True,s=False )
    curve.ws[0] >> ikCtrl.cr
    curve.ws[0] // ikCtrl.cr
    pm.delete(curve.getParent())

cmds.delete('IKOffsetSpine2_M_parentConstraint1','IKOffsetSpine3_M_parentConstraint1','IKOffsetSpine4_M_parentConstraint1','IKSpineFix_Grp')

MMList = []
IKcvOffsetList = []
for i in range(1,3):
    for o in range(1,7):
        MM = 'IKcvOffsetSpine{}MM{}_M'.format(o,i)
        MMList.append(MM)
        IKcvOffset = 'IKcvOffsetSpine{}_M'.format(o)
        matA_list = cmds.xform(IKcvOffset, q=True, ws=True, matrix=True)
        IKcvOffsetList.append(matA_list)

for dr, dn in list(zeroIK.items()):
    cmds.matchTransform(dn[0], dr, pos=1, rot=1, scl=1)
    cmds.matchTransform(dn[1], 'IKhybridSpine1_M', pos=0, rot=1, scl=0)
    ikCtrl_shape_fix(pm.PyNode('IKSpine{}_M'.format(dr.split('_')[0][-1])))
ikCtrl_shape_fix(pm.PyNode('IKExtraSpine1_M'))

for matA,MM in list(zip(IKcvOffsetList,MMList)):
    X = cmds.listConnections(MM+'.matrixIn[1]',d=False)
    matB = cmds.xform(X, q=True, ws=True, matrix=True)
    rel_matrix = get_relative_matrix(matA, matB)
    cmds.setAttr("{}.matrixIn[0]".format(MM), rel_matrix, type="matrix")

cmds.parentConstraint('IKFollowEndSpine1_M','IKFollowEndSpine5_M','IKOffsetSpine2_M',mo=True)
cmds.parentConstraint('IKFollowEndSpine1_M','IKFollowEndSpine5_M','IKOffsetSpine3_M',mo=True)
cmds.parentConstraint('IKFollowEndSpine1_M','IKFollowEndSpine5_M','IKOffsetSpine4_M',mo=True)

if __name__ == "__main__":
    run()

