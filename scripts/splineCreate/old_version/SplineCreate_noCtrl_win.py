import pymel.core as pm

def mkGroups(name, count=1):
    nodes = []
    for i in range(count):
        nodes.append(pm.createNode('transform', name='{}_{}_oft'.format(name, i+1)))
    return nodes

def setparents(nodes):
    count = len(nodes)
    for i in range(1, count):
        pm.parent(nodes[i-1], nodes[i])

def setGsParents(_grps):
    count = len(_grps)
    for i in range(1, count):
        pm.parent(_grps[count - i][-1], _grps[count - i - 1][0])

def matchPositions(obja, objb):
    pm.delete(pm.parentConstraint(obja, objb))

def mkGroupAndSetParents(obj, exname, count):
    pnodes = []
    if count > 0:
        pnodes = mkGroups(str(obj) + exname, count=count)
        setparents(pnodes)
        matchPositions(obj, pnodes[-1])
    return pnodes

def createShape(s=5, r=1, d=1):
    tnode = pm.circle(nr=[1,0,0], d=d, s=s, r=r)[0]
    pm.delete(tnode, ch=True)
    return tnode,tnode.getShape()

def addCurveShape(obj, **kw):
    tnode, tshape = createShape(**kw)
    pm.parent(tshape, obj, add=True, s=True)
    pm.delete(tnode)
    tshape.rename('{}Shape'.format(obj))

def lockAndHideAttrs(obj, attrs=['sx', 'sy', 'sz', 'v']):
    for attr in attrs:
        pm.setAttr('{}.{}'.format(obj, attr), lock=True, keyable=False, channelBox=False)

def createFollicle(nubSurface, name, pv, pu):
    fshape = pm.createNode('follicle')
    ftrans = fshape.getParent()
    ftrans.rename(name)
    fshape.outTranslate >> ftrans.t
    fshape.outRotate >> ftrans.r
    nubSurface.worldMatrix >> fshape.inputWorldMatrix
    nubSurface.local >> fshape.inputSurface
    fshape.parameterV.set(pv)
    fshape.parameterU.set(pu)
    return ftrans

def createConditionRig(nubs_surface, global_scale_attr):
    nubs_surface_shape = nubs_surface.getShape()
    dup_curve_results = pm.duplicateCurve(nubs_surface_shape.v[0.5], ch=True, rn=False, local=False)
    dup_curve = pm.PyNode(dup_curve_results[0])
    dup_curve.v.set(0,l=True)
    dup_curve_shape = dup_curve.getShape()

    curveInfo = pm.arclen(dup_curve_shape, ch=True)
    length = curveInfo.arcLength.get()

    mul_node = pm.createNode('multDoubleLinear')
    mul_node.input1.set(length)
    global_scale_attr >> mul_node.input2

    muld_node = pm.createNode('multiplyDivide')
    muld_node.operation.set(2)  

    curveInfo.arcLength >> muld_node.input1X

    mul_node.output >> muld_node.input2X

    cnd_node = pm.createNode('condition')

    cnd_node.operation.set(5)  
    cnd_node.colorIfTrueR.set(1)

    curveInfo.arcLength >> cnd_node.firstTerm
    mul_node.output >> cnd_node.secondTerm
    muld_node.outputX >> cnd_node.colorIfFalseR
    return nubs_surface_shape, dup_curve_shape, cnd_node

def createStretchAbleRig(nubs_surface_shape, dup_curve_shape, cnd_node, index_value, out_node, stretch_attr):
    divi_node = pm.createNode('multiplyDivide')
    divi_node.operation.set(2)
    divi_node.input1X.set(index_value)

    cnd_node.outColorR >> divi_node.input2X

    blend_node = pm.createNode('blendColors')
    divi_node.input1X >> blend_node.color1R
    divi_node.outputX >> blend_node.color2R
    stretch_attr >> blend_node.blender

    mp_node = pm.createNode('motionPath')
    mp_node.inverseFront.set(1)
    mp_node.fractionMode.set(1)
    mp_node.frontAxis.set(2)
    mp_node.upAxis.set(0)

    dup_curve_shape.worldSpace[0] >> mp_node.geometryPath
    blend_node.outputR >> mp_node.uValue

    cpos_node = pm.createNode('closestPointOnSurface')

    mp_node.allCoordinates >> cpos_node.inPosition

    nubs_surface_shape.worldSpace[0] >> cpos_node.inputSurface

    posi_node = pm.createNode('pointOnSurfaceInfo')

    nubs_surface_shape.worldSpace[0] >> posi_node.inputSurface

    cpos_node.parameterU >> posi_node.parameterU
    cpos_node.parameterV >> posi_node.parameterV

    posi_node.position >> out_node.t

    aim_node = pm.createNode('aimConstraint')
    posi_node.normal >> aim_node.target[0].targetTranslate
    posi_node.tangentU >> aim_node.worldUpVector
    aim_node.constraintRotate >> out_node.r
    return aim_node

def main(obj_list, subJntCount, 
         grp_type_list=['org', 'pxy', 'ctl'],
         fk_arg_info={'org':4, 'pxy':2, 'ctl':5},
         ik_arg_info={'org':1, 'pxy':0, 'ctl':3}):
    
    base_value = 1
    try:
        s_position = obj_list[0].getTranslation(space='world')
        e_position = obj_list[-1].getTranslation(space='world')
        base_value = s_position.distanceTo(e_position) * 0.03
    except:
        pass

    base_name = str(obj_list[0])
    '''
    fk_grp_list = {x:[] for x in grp_type_list}
    for gtype in grp_type_list:
        for obj in obj_list:
            fk_grp_list[gtype].append(mkGroupAndSetParents(obj, '_' + gtype + '_fk', fk_arg_info.get(gtype)))

    ik_grp_list = {x:[] for x in grp_type_list}
    for gtype in grp_type_list:
        for obj in obj_list:
            ik_grp_list[gtype].append(mkGroupAndSetParents(obj, '_' + gtype + '_ik', ik_arg_info.get(gtype)))

    for gtype in grp_type_list:
        for fks, iks in zip(fk_grp_list.get(gtype, []), ik_grp_list.get(gtype, [])):
            if len(iks):
                pm.parent(iks[-1], fks[0])
    
    for gtype in grp_type_list:
        setGsParents(fk_grp_list[gtype])

    for grps in fk_grp_list.get('ctl'):
        addCurveShape(grps[0], s=6, r=1, d=3)
        lockAndHideAttrs(grps[0])

    for grps in ik_grp_list.get('ctl'):
        addCurveShape(grps[0], s=3, r=1, d=1)
        lockAndHideAttrs(grps[0])

    proxySurfaces = []
    proxySurfaceGrp = pm.createNode('transform', name='{}_proxySurface_grp'.format(base_name))
    for obj in obj_list:
        proxySf = pm.nurbsPlane(ax=[0, 0, 1], w=base_value * 2)[0]
        proxySf.rename(str(obj) + '_skin_surface')
        pm.delete(proxySf, ch=True)
        proxySurfaces.append(proxySf)
        matchPositions(obj, proxySf)
    
    pm.parent(proxySurfaces, proxySurfaceGrp)

    proxyFollicles = []
    for pfurface in proxySurfaces:
        node = createFollicle(pfurface, pfurface + '_fol', 0.5, 0.5)
        proxyFollicles.append(node)

    pm.parent(proxyFollicles, proxySurfaceGrp)

    for pxf, pxyFks in zip(proxyFollicles, fk_grp_list.get('pxy')):
        pm.parentConstraint(pxf, pxyFks[-2], mo=True)

    for pxyFks, ctlFks in zip(fk_grp_list.get('pxy'), fk_grp_list.get('ctl')):
        pxyFks[-2].t >> ctlFks[-2].t
        pxyFks[-2].r >> ctlFks[-2].r
    if fk_grp_list.get('org'):
        for ctlFks, orgFks in zip(fk_grp_list.get('ctl'), fk_grp_list.get('org')):
            for i in range(fk_arg_info.get('org')-1):
                ctlFks[i].t >> orgFks[i].t
                ctlFks[i].r >> orgFks[i].r
    if ik_grp_list.get('org'):
        for ctlFks, orgFks in zip(ik_grp_list.get('ctl'), ik_grp_list.get('org')):
            ctlFks[0].t >> orgFks[0].t
            ctlFks[0].r >> orgFks[0].r

    orgJnts = []

    if ik_grp_list.get('org'):
        jnt_follow_objs = ik_grp_list.get('org')
    else:
        jnt_follow_objs = ik_grp_list.get('ctl')

    for obj, orgiks in zip(obj_list, jnt_follow_objs):
        jnt = pm.createNode('joint', name=str(obj) + '_org_jnt')
        pm.parent(jnt, orgiks[0])
        matchPositions(orgiks[0], jnt)
        pm.makeIdentity(jnt, apply=True)
        orgJnts.append(jnt)
    '''
    curves = []
    for obj in obj_list:
        curve = pm.curve(d=1, p=[(0, 0, base_value), (0, 0, -base_value)])
        curves.append(curve)
        matchPositions(obj, curve)
        
    nubSurface = pm.loft(curves, name=base_name + '_nubSurfaces')[0]
    pm.delete(nubSurface, ch=True)
    pm.delete(curves)
    
    orgRigGrp = pm.createNode('transform', name='{}_orgRigObject_grp'.format(base_name))
    pm.parent(nubSurface, orgRigGrp)
    nubSurfaceShape = nubSurface.getShape()
    #pm.select(orgJnts, nubSurface)
    #pm.mel.eval('newSkinCluster "-toSelectedBones -bindMethod 0 -normalizeWeights 1 -weightDistribution 0 -mi 1 -dr 10 -rui 0,multipleBindPose,1";')

    cpos = pm.createNode('closestPointOnSurface')
    nubSurfaceShape.worldSpace >> cpos.inputSurface
    endPos = pm.xform(obj_list[-1], q=True, ws=True, t=True)
    cpos.inPosition.set(endPos)

    maxParU = cpos.parameterU.get()
    pm.delete(cpos)
    
    stepValue = maxParU / subJntCount
    normalValue = stepValue / maxParU
    ftransList = []
    sgrps = []
    mode = 1
    top_grp = pm.createNode('transform', name='{}_rig_all_grp'.format(base_name))
    rigNoTranGrp = pm.createNode('transform', name='{}_rigNoTranslate_grp'.format(base_name))

    if mode == 0:
        for i in range(subJntCount+1):
            ftrans = createFollicle(nubSurface, '{}_skin_{}_fol'.format(base_name, i+1), 0.5, stepValue * i / maxParU)
            ftransList.append(ftrans)
            sgrp = pm.createNode('transform', name='{}_skin_{}_oft'.format(base_name, i+1))
            sjnt = pm.createNode('joint', name='{}_skin_{}_fol'.format(base_name, i+1))
            pm.parent(sjnt, sgrp)
            ftrans.t >> sgrp.t
            ftrans.r >> sgrp.r
            sgrps.append(sgrp)

        ftransList[0].getShape().parameterU.set(normalValue * 0.01)
        ftransList[-1].getShape().parameterU.set(1-(normalValue * 0.01))
        pm.parent(ftransList, orgRigGrp)
    elif mode == 1:
        attr_name_list = ['global_scale', 'ik_vis', 'fk_vis', 'stretch']
        attr_kws = {'global_scale':{'dv':1, 'min':0.01, 'max':10},
                    'ik_vis':{'dv':0, 'min':0, 'max':1},
                    'fk_vis':{'dv':1, 'min':0, 'max':1},
                    'stretch':{'dv':0, 'min':0, 'max':1}}
        attr_info = {}
        for attr_name in attr_name_list:
            attr_info[attr_name] = addAttr(top_grp, attr_name, **attr_kws.get(attr_name, {}))
        
        ik_vis_attr = attr_info.get('ik_vis')
        '''
        if ik_vis_attr:
            for grps in ik_grp_list.get('ctl'):
                shape = grps[0].getShape(type='nurbsCurve')
                if shape:
                    ik_vis_attr >> shape.v

            #ik_grp_list.get('ctl')[-1][0].lodVisibility.set(0)
        '''
        fk_vis_attr = attr_info.get('fk_vis')
        '''
        if fk_vis_attr:
            for grps in fk_grp_list.get('ctl'):
                shape = grps[0].getShape(type='nurbsCurve')
                if shape:
                    fk_vis_attr >> shape.v
        '''
        index_value_list = []
        for i in range(subJntCount+1):
            index_value_list.append(stepValue * i / maxParU)
        index_value_list[0] = normalValue * 0.01
        index_value_list[-1] = 1 - (normalValue * 0.01)

        global_scale_attr = attr_info['global_scale']
        stretch_attr = attr_info.get('stretch')
        fk_end_ctl = nubSurface

        fk_end_ctl_attr = addAttr(fk_end_ctl, 'stretch', **attr_kws.get('stretch'))
        fk_end_ctl_attr >> stretch_attr

        nubs_surface_shape, dup_curve_shape, cnd_node = createConditionRig(nubSurface, global_scale_attr)
        aim_node_list = []
        for i in range(subJntCount+1):
            index_value = index_value_list[i]

            sgrp = pm.createNode('transform', name='{}_skin_{}_oft'.format(base_name, i+1))
            sjnt = pm.createNode('joint', name='{}_skin_{}_fol'.format(base_name, i+1))
            pm.parent(sjnt, sgrp)
            sgrps.append(sgrp)
            aim_node = createStretchAbleRig(nubs_surface_shape, dup_curve_shape, cnd_node, index_value, sgrp, stretch_attr)
            aim_node_list.append(aim_node)
            global_scale_attr >> sgrp.sx
            global_scale_attr >> sgrp.sy
            global_scale_attr >> sgrp.sz
        dup_curve = dup_curve_shape.getParent()
        dup_curve.inheritsTransform.set(0)
        pm.parent(dup_curve, aim_node_list, rigNoTranGrp)
    skGrp = pm.createNode('transform', name='{}_skinJnt_grp'.format(base_name))
    pm.parent(sgrps, skGrp)

    pm.parent(orgRigGrp, rigNoTranGrp)
    pm.parent(skGrp, rigNoTranGrp, top_grp)
    '''
    for grps in list(fk_grp_list.values()):
        pm.parent(grps[0][-1], top_grp)
    '''
    pm.select(cl=True)

def addAttr(node, attr_name, **kw):
    if not node.hasAttr(attr_name):
        node.addAttr(attr_name, **kw)
        attr = node.attr(attr_name)
        attr.showInChannelBox(True)
        attr.setKeyable(True)
    else:
        attr = node.attr(attr_name)
    return attr

class Win(object):
    wname = 'subSplineControl_tool_win'
    title = 'Spline Create'

    def __init__(self):
        self.win = None

    def close(self):
        try:
            pm.deleteUI(self.wname)
        except:
            pass
    def show(self):
        self.close()
        self.win = pm.window(self.wname, title=self.title, s=False)
        with self.win:
            with pm.columnLayout(adj=True,co=['both',10]):
                self.mkMainLayout()
    
    def mkMainLayout(self):
        self.mode_rbg = pm.radioButtonGrp(cw=[1,85],select=1, label='Hierarchy', labelArray2=['selected', 'Below'], numberOfRadioButtons=2)
        pm.separator(h=5, style='none')
        self.create_type_rbg = pm.radioButtonGrp(cw=[1,85],select=1, label='Create type', labelArray2=['Sub control', 'Normal control'], numberOfRadioButtons=2)
        pm.separator(h=5, style='none')
        self.skinJntCount = pm.floatSliderGrp(cw=[1,85], label='Sub joint count', field=True, minValue=0.5, maxValue=4, fieldMinValue=0.5, fieldMaxValue=30, value=2)
        pm.button(l='Go', c=lambda *args: self.create())
        pm.separator(h=10, style='none')

    def create(self):
        sels = pm.ls(sl=True)
        if not len(sels):
            pm.warning('No objects selected to rigging.')
            return
        
        mode = self.mode_rbg.getSelect()
        create_type = self.create_type_rbg.getSelect()
        count = int(self.skinJntCount.getValue())
        objlists = []
        if mode == 1:
            objlists = [sels]
        else:
            for sel in sels:
                objlists.append(pm.ls(sel, dag=True, type='transform'))

        if create_type == 1:
            grp_type_list = ['org', 'pxy', 'ctl']
            fk_arg_info = {'org':4, 'pxy':2, 'ctl':5}
            ik_arg_info = {'org':1, 'pxy':0, 'ctl':3}
        else:
            grp_type_list = ['pxy', 'ctl']
            fk_arg_info = {'pxy':2, 'ctl':5}
            ik_arg_info = {'pxy':0, 'ctl':3}

        for objs in objlists:
            objCount = len(objs)
            if objCount > 1:
                subJntCount = int((objCount - 1) * count)
                main(objs, subJntCount, grp_type_list=grp_type_list,
                     fk_arg_info=fk_arg_info, ik_arg_info=ik_arg_info)
            else:
                pm.warning('locator object least 2')

if __name__ == '__main__':
    self = Win()
    self.show()
    #sels = pm.ls(sl=True)
    #main(sels,8)