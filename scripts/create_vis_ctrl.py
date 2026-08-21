# _*_ coding: utf-8 _*_
# Instruction: create vis ctrl
# Author: WangRuiLong

import pymel.core as pm
import maya.api.OpenMaya as om2

GRP_BASE_NAMES = ['visibility_ctrl', 'visibility_move', 'visibility_zero']
NAME_PATTERN = '{}'
BASE_ATTR_DATA = [
    ['meshDisplayType',0,{'at':'enum','en':'Normal:Template:Reference'},0,1,0],
    ['modelVis',1,{'at':'bool'},1,0,0],
    ['visSep',0,{'at':'enum','en':'Vis','nn':'_______________'},0,1,1],
    ['faceCtrlVis',1,{'at':'bool'},0,1,0],
    ['faceSecCtrlVis',0,{'at':'bool'},0,1,0],
]
MESH_DISPLAY_TYPE_ATTR_NAME = 'meshDisplayType'
MESH_DISPLAY_ATTR_NAME = 'modelVis'

def pick_matrix(matrix, t=False, r=False, s=False, sh=False):
    # 确保输入为 MMatrix
    if not isinstance(matrix, om2.MMatrix):
        matrix = om2.MMatrix(matrix)
    
    # 分解原矩阵
    tfm = om2.MTransformationMatrix(matrix)
    
    # 提取各分量
    translation = tfm.translation(om2.MSpace.kWorld)   # MVector
    rotation_quat = tfm.rotation(asQuaternion=True)           # MQuaternion 
    scale = tfm.scale(om2.MSpace.kWorld)               # MVector
    shear = tfm.shear(om2.MSpace.kWorld)               # MVector (xy, xz, yz)
    
    # 新建一个单位变换矩阵对象
    new_tfm = om2.MTransformationMatrix()
    
    # 按需设置分量
    if t:
        new_tfm.setTranslation(translation, om2.MSpace.kWorld)
    if r:
        new_tfm.setRotation(rotation_quat)              # 直接设置四元数
    if s:
        new_tfm.setScale(scale, om2.MSpace.kWorld)
    if sh:
        new_tfm.setShear(shear, om2.MSpace.kWorld)
    
    return new_tfm.asMatrix()

def get_shape_pivot(obj):
    """将点 (x,y,z) 转换为平移矩阵(MMatrix)"""
    bboxCenter = pm.getAttr(obj+'.center')
    tfm = om2.MTransformationMatrix()
    tfm.setTranslation(om2.MVector(bboxCenter), om2.MSpace.kTransform)
    bboxM = tfm.asMatrix()
    shapePivot = om2.MMatrix(pick_matrix(obj.xformMatrix.get(),0,1,1,1)) * om2.MMatrix(bboxM) * om2.MMatrix(obj.xformMatrix.get().inverse())
    return list(shapePivot)

def create_text_control(name,parent=None,txt_grp=None,center_pivot=True,create_border=False):
    if txt_grp is None:
        txt_grp = pm.PyNode(pm.textCurves(t=name, f='Times New Roman')[0])
        # txt_grp.s.set(1.3,1.3,1.3)
    
    if center_pivot:
        #bbox = txt_grp.getBoundingBox(space='world')
        pm.xform(txt_grp, cpc=True)
        rp = txt_grp.getRotatePivot(space='world')
        pm.xform(txt_grp, ws=True, t=rp * -1)

    transforms = pm.ls(txt_grp, dag=True, type='transform')
    for transform in transforms:
        pm.delete(transform.inputs())
    pm.makeIdentity(txt_grp, a=True, t=1, r=1, s=1)

    curveShapes = pm.ls(txt_grp, dag=True, type='nurbsCurve')
    for curveShape in curveShapes:
        curveShape.ihi.set(0)
        curveShape.hiddenInOutliner.set(1)

    del_nodes = [txt_grp]
    if create_border:
        bbox = txt_grp.getBoundingBox(space='world')
        bminX = bbox.min().x * 1.1
        bmaxX = bbox.max().x * 1.1
        bminY = bbox.min().y * 1.3
        bmaxY = bbox.max().y * 1.3
        border_curve = pm.curve(d=1, p=[(bminX, bminY, 0), (bmaxX, bminY, 0), (bmaxX, bmaxY, 0), (bminX, bmaxY, 0), (bminX, bminY, 0)])
        curveShapes.insert(0, border_curve.getShape())
        del_nodes.append(border_curve)

    if parent is None:
        parent = pm.createNode('transform')
    else:
        shapePivotM = get_shape_pivot(parent)
        if parent.getShapes():
            pm.delete(parent.getShapes())
        pm.xform(txt_grp, ws=True, matrix=shapePivotM)
        pm.makeIdentity(txt_grp, a=True, t=1, r=1, s=1)
        if create_border:
            pm.xform(border_curve, ws=True, matrix=shapePivotM)
            pm.makeIdentity(border_curve, a=True, t=1, r=1, s=1)

    for curveShape in curveShapes:
        curveShape.overrideEnabled.set(1)
        curveShape.overrideColor.set(17)
        pm.parent(curveShape, parent, add=True, shape=True)
    
    parent_name = str(parent)
    shapes = parent.getShapes()
    for shape in shapes:
        shape.rename('{}Shape'.format(parent_name))
    
    pm.delete(del_nodes)
    return parent

def create_control_group(name, name_pattern=None,base_names=None, attr_args=None):
    if name_pattern is None:
        name_pattern = NAME_PATTERN
    
    txt_name = name_pattern.format(name)
    
    if base_names is None:
        base_names = GRP_BASE_NAMES
    
    pm.select(clear=True)
    grps = [pm.group(n=base_name) for base_name in base_names]

    control = create_text_control(txt_name, parent=grps[0])

    def_attrs = control.listAttr(k=True)

    for def_attr in def_attrs:
        def_attr.setKeyable(False)
        def_attr.setLocked(True)

    if attr_args is None:
        attr_args = BASE_ATTR_DATA

    _setattrs = [('setKeyable', False), ('showInChannelBox', True)]
    for attr_arg in attr_args:
        control.addAttr(attr_arg[0], **attr_arg[2])
        attr = control.attr(attr_arg[0])
        attr.set(attr_arg[1])
        
        attr.setKeyable(attr_arg[3])
        attr.showInChannelBox(attr_arg[4])
        attr.setLocked(attr_arg[5])
    
    return grps

def get_name_dialog():
    result = pm.promptDialog(t='', m='Enter Name:', b=['OK', 'Cancel'], db='OK', cb='Cancel',ds='Cancel')
    if result == 'OK':
        return pm.promptDialog(q=True, text=True)
    
def create_control_group_dialog(**kwargs):
    name = get_name_dialog()
    if name is None:
        return
    return create_control_group(name, **kwargs)

def connect_meshDisplayType(control_attr=None):
    sels = pm.ls(sl=True)
    if len(sels) < 2:
        pm.warning('Select vis ctrl and some transforms, and retry!')
        return

    if control_attr is None:
        control_attr = MESH_DISPLAY_TYPE_ATTR_NAME

    attr_arg = BASE_ATTR_DATA[0]

    control = sels[0]
    if not control.hasAttr(control_attr):
        if control.hasAttr('mesh_display_type'):
            pm.renameAttr(control.attr('mesh_display_type'),control_attr)
            pm.warning('Rename attr: {}'.format(control_attr))
        else:
            control.addAttr(control_attr, **attr_arg[2])
            pm.warning('Add attr: {}'.format(control_attr))
    
    control_attr = control.attr(control_attr)
    control_attr.set(attr_arg[1])
    control_attr.setKeyable(attr_arg[3])
    control_attr.showInChannelBox(attr_arg[4])
    control_attr.setLocked(attr_arg[5])
    for sel in sels[1:]:
        sel.overrideEnabled.set(1)
        control_attr >> sel.overrideDisplayType

def connect_modelVis(control_attr=None):
    sels = pm.ls(sl=True)
    if len(sels) < 2:
        pm.warning('Select vis ctrl and some transforms, and retry!')
        return

    if control_attr is None:
        control_attr = MESH_DISPLAY_ATTR_NAME

    attr_arg = BASE_ATTR_DATA[1]

    control = sels[0]
    if not control.hasAttr(control_attr):
        control.addAttr(control_attr, **attr_arg[2])
        pm.warning('Add attr: {}'.format(control_attr))
    
    control_attr = control.attr(control_attr)
    control_attr.set(attr_arg[1])
    control_attr.setKeyable(attr_arg[3])
    control_attr.showInChannelBox(attr_arg[4])
    control_attr.setLocked(attr_arg[5])
    for sel in sels[1:]:
        control_attr >> sel.v

def rebuild_shape(name_pattern=None):
    sels = pm.ls(sl=True)
    if not len(sels):
        pm.warning('Select vis ctrl, and retry!')
        return

    if name_pattern is None:
        name_pattern = NAME_PATTERN

    for sel in sels:
        name = get_name_dialog()
        if name:
            txt_name = name_pattern.format(name)
            create_text_control(txt_name, parent=sel)
    
if __name__ == '__main__':
    #create_control_group_dialog()       # create VIS
    #connect_meshDisplayType()           # connect mesh display type
    #connect_modelVis()                 # connect model visibility
    rebuild_shape()                     # rebuild VIS