# _*_ coding: utf-8 _*_
# Instruction: create vis ctrl
# Author: WangRuiLong

import pymel.core as pm
import maya.api.OpenMaya as om2
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

def create_text_control(name,view=None,parent=None,txt_grp=None,center_pivot=True,create_border=False):
    if txt_grp is None:
        if view is None:
            view = name
        txt_grp = pm.PyNode(pm.textCurves(t=view, f='Times New Roman')[0])
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
        parent = pm.createNode('transform',n=name)
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

def create_from_ui(name_field, view_field, create_border_check):
    name = name_field.getText().strip()
    view = view_field.getText().strip()
    if not name:
        pm.warning('Name cannot be empty!')
        return
    if not view:
        view = name
    create_text_control(name, view=view, create_border=create_border_check.getValue())


def rebuild_from_ui(name_field, view_field, create_border_check):
    sels = pm.ls(sl=True)
    if not sels:
        pm.warning('Select vis ctrl, and retry!')
        return

    name = name_field.getText().strip()
    view = view_field.getText().strip()
    if not name:
        pm.warning('Name cannot be empty!')
        return
    if not view:
        view = name

    for sel in sels:
        create_text_control(name, view=view, parent=sel, create_border=create_border_check.getValue())


def build_text_control_ui():
    win_name = 'textCrv_main_ui'

    if pm.window(win_name, q=True, exists=True):
        pm.deleteUI(win_name, window=True)

    win = pm.window(win_name, title='Text Control', widthHeight=(340, 200), sizeable=False)
    with win:
        with pm.columnLayout(adjustableColumn=True, rowSpacing=6, columnAlign='left'):
            name_field = pm.textFieldGrp(label='Name', text='VIS', columnWidth2=(60, 240))
            view_field = pm.textFieldGrp(label='View', text='front', columnWidth2=(60, 240))
            create_border_check = pm.checkBox(label='create border', value=False)
            with pm.rowLayout(nc=2, cw2=(150, 150), columnAlign2=('center', 'center')):
                pm.button(label='Create', command=lambda *_: create_from_ui(name_field, view_field, create_border_check))
                pm.button(label='Rebuild', command=lambda *_: rebuild_from_ui(name_field, view_field, create_border_check))

    pm.showWindow(win)
    pm.setFocus(name_field)
    return win


if __name__ == '__main__':
    build_text_control_ui()